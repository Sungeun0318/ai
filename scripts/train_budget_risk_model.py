"""예산 초과 위험도 RandomForest 학습 스크립트.

seed/*.csv 샘플 데이터를 방 단위 feature로 집계한 뒤
LOW / MEDIUM / HIGH 위험도 라벨을 학습한다.

실행:
    python scripts/train_budget_risk_model.py
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
import joblib


# 0. 기본 설정

RANDOM_STATE = 42
FEATURE_COLUMNS = [
    "total_budget",
    "member_count",
    "spent_amount",
    "remaining_budget",
    "receipt_count",
    "avg_receipt_amount",
    "max_receipt_amount",
    "good_price_usage_rate",
    "budget_usage_rate",
    "combined_count",
    "split_count",
    "personal_count",
    "avg_member_budget",
    "min_member_budget",
    "max_member_budget",
    "location",
    "tag",
    "status",
]
NUMERIC_FEATURES = [
    "total_budget",
    "member_count",
    "spent_amount",
    "remaining_budget",
    "receipt_count",
    "avg_receipt_amount",
    "max_receipt_amount",
    "good_price_usage_rate",
    "budget_usage_rate",
    "combined_count",
    "split_count",
    "personal_count",
    "avg_member_budget",
    "min_member_budget",
    "max_member_budget",
]
CATEGORICAL_FEATURES = ["location", "tag", "status"]


# 1. 데이터 로드

def load_seed(seed_dir: Path) -> dict[str, pd.DataFrame]:
    """seed 폴더의 CSV 파일을 DataFrame으로 읽어온다."""

    files = {
        "rooms": "rooms.csv",
        "room_budget_results": "room_budget_results.csv",
        "room_purpose_tags": "room_purpose_tags.csv",
        "receipts": "receipts.csv",
        "budget": "budget.csv",
    }
    data = {}
    for key, filename in files.items():
        path = seed_dir / filename
        if not path.exists():
            raise FileNotFoundError(f"필수 seed 파일이 없습니다: {path}")
        data[key] = pd.read_csv(path, encoding="utf-8-sig")
    return data


# 2. 전처리 / Feature 생성

def build_features(data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """여러 CSV를 room_no 기준의 방 단위 feature 테이블로 변환한다."""

    # 2-1. 원본 데이터 복사
    rooms = data["rooms"].copy()
    budget_results = data["room_budget_results"].copy()
    tags = data["room_purpose_tags"].copy()
    receipts = data["receipts"].copy()
    budgets = data["budget"].copy()

    # 2-2. 조인 기준 컬럼 타입 정리
    rooms["room_no"] = rooms["room_no"].astype(int)
    budget_results["room_no"] = budget_results["room_no"].astype(int)
    tags["room_no"] = tags["room_no"].astype(int)
    receipts["room_no"] = receipts["room_no"].astype(int)
    budgets["room_no"] = budgets["room_no"].astype(int)

    # 2-3. 영수증 데이터 전처리
    # amount는 숫자로 변환하고, 변환 실패/결측값은 0으로 처리한다.
    receipts["amount"] = pd.to_numeric(receipts["amount"], errors="coerce").fillna(0)
    receipts["good_price_matched"] = pd.to_numeric(receipts["good_price_matched"], errors="coerce").fillna(0)

    # receipt_type은 문자열 카테고리라 모델이 바로 쓰기 어렵다.
    # 그래서 COMBINED/SPLIT/PERSONAL 여부를 각각 0/1 컬럼으로 변환한다.
    receipt_type_dummies = pd.get_dummies(receipts["receipt_type"], prefix="receipt_type")
    receipt_stats_source = pd.concat([receipts[["room_no", "amount", "good_price_matched"]], receipt_type_dummies], axis=1)
    for column in ["receipt_type_COMBINED", "receipt_type_SPLIT", "receipt_type_PERSONAL"]:
        if column not in receipt_stats_source:
            receipt_stats_source[column] = 0

    # 2-4. 방별 영수증 집계
    # 예측 대상은 개별 영수증이 아니라 "방의 위험도"이므로 room_no 기준으로 묶는다.
    receipt_stats = receipt_stats_source.groupby("room_no").agg(
        spent_amount=("amount", "sum"),
        receipt_count=("amount", "count"),
        avg_receipt_amount=("amount", "mean"),
        max_receipt_amount=("amount", "max"),
        good_price_count=("good_price_matched", "sum"),
        combined_count=("receipt_type_COMBINED", "sum"),
        split_count=("receipt_type_SPLIT", "sum"),
        personal_count=("receipt_type_PERSONAL", "sum"),
    ).reset_index()
    receipt_stats["good_price_usage_rate"] = (
        receipt_stats["good_price_count"] / receipt_stats["receipt_count"].clip(lower=1) * 100
    )

    # 2-5. 방별 멤버 예산 집계
    budget_stats = budgets.groupby("room_no").agg(
        avg_member_budget=("amount", "mean"),
        min_member_budget=("amount", "min"),
        max_member_budget=("amount", "max"),
    ).reset_index()

    # 2-6. 방 정보 + 예산 결과 + 태그 + 영수증 집계 + 멤버 예산 집계 결합
    feature_df = rooms[["room_no", "room_name", "location", "status", "total_budget"]].merge(
        budget_results[["room_no", "member_count"]],
        on="room_no",
        how="left",
    )
    feature_df = feature_df.merge(tags[["room_no", "tag_tags"]], on="room_no", how="left")
    feature_df = feature_df.merge(receipt_stats, on="room_no", how="left")
    feature_df = feature_df.merge(budget_stats, on="room_no", how="left")

    # 2-7. 결측값 처리
    # 영수증이 없는 방은 집계값이 NaN이 되므로 0으로 채운다.
    feature_df = feature_df.rename(columns={"tag_tags": "tag"})
    fill_zero_columns = [
        "member_count",
        "spent_amount",
        "receipt_count",
        "avg_receipt_amount",
        "max_receipt_amount",
        "good_price_count",
        "good_price_usage_rate",
        "combined_count",
        "split_count",
        "personal_count",
        "avg_member_budget",
        "min_member_budget",
        "max_member_budget",
    ]
    for column in fill_zero_columns:
        feature_df[column] = pd.to_numeric(feature_df[column], errors="coerce").fillna(0)
    feature_df["total_budget"] = pd.to_numeric(feature_df["total_budget"], errors="coerce").fillna(0)

    # 2-8. 파생 변수 생성
    # 예산 사용률은 예산 초과 위험도를 판단하는 핵심 feature다.
    feature_df["remaining_budget"] = (feature_df["total_budget"] - feature_df["spent_amount"]).clip(lower=0)
    feature_df["budget_usage_rate"] = (
        feature_df["spent_amount"] / feature_df["total_budget"].replace(0, pd.NA) * 100
    ).fillna(0)
    feature_df["location"] = feature_df["location"].fillna("미분류")
    feature_df["tag"] = feature_df["tag"].fillna("미분류")
    feature_df["status"] = feature_df["status"].fillna("UNKNOWN")

    # 2-9. 정답 라벨 생성
    # LOW / MEDIUM / HIGH 라벨을 만들어 분류 모델이 학습할 수 있게 한다.
    feature_df["risk_label"] = feature_df["budget_usage_rate"].apply(to_risk_label)

    return feature_df


# 3. 라벨 생성 기준

def to_risk_label(usage_rate: float) -> str:
    """예산 사용률을 기준으로 위험도 라벨을 만든다."""

    if usage_rate >= 100:
        return "HIGH"
    if usage_rate >= 60:
        return "MEDIUM"
    return "LOW"


# 4. 모델 학습 / 하이퍼파라미터 튜닝

def train_model(feature_df: pd.DataFrame) -> tuple[Pipeline, dict]:
    """RandomForest 모델을 학습하고 평가 지표를 반환한다."""

    # 4-1. 입력 feature와 정답 label 분리
    x = feature_df[FEATURE_COLUMNS]
    y = feature_df["risk_label"]

    # 4-2. 학습/테스트 데이터 분리
    # random_state=42로 매번 같은 결과가 나오도록 고정한다.
    x_train, x_test, y_train, y_test = train_test_split(
        x,
        y,
        test_size=0.2,
        random_state=RANDOM_STATE,
        stratify=y,
    )

    # 4-3. 숫자형/범주형 컬럼 전처리
    # 숫자형은 스케일링하고, 범주형은 One-Hot Encoding으로 변환한다.
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), NUMERIC_FEATURES),
            ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES),
        ]
    )

    # 4-4. 전처리 + 모델을 하나의 Pipeline으로 구성
    pipeline = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            (
                "model",
                RandomForestClassifier(
                    random_state=RANDOM_STATE,
                    class_weight="balanced",
                ),
            ),
        ]
    )

    # 4-5. 하이퍼파라미터 후보
    # GridSearchCV가 여러 조합을 비교해서 가장 정확도가 높은 설정을 찾는다.
    param_grid = {
        "model__n_estimators": [100, 200, 300],
        "model__max_depth": [4, 6, 8, None],
        "model__min_samples_split": [2, 5],
        "model__min_samples_leaf": [1, 2],
    }
    grid = GridSearchCV(
        pipeline,
        param_grid=param_grid,
        cv=5,
        scoring="accuracy",
        n_jobs=1,
    )
    grid.fit(x_train, y_train)

    # 4-6. 테스트 데이터로 최종 성능 평가
    best_model = grid.best_estimator_
    predictions = best_model.predict(x_test)
    accuracy = accuracy_score(y_test, predictions)

    metrics = {
        "random_state": RANDOM_STATE,
        "row_count": int(len(feature_df)),
        "train_count": int(len(x_train)),
        "test_count": int(len(x_test)),
        "accuracy": round(float(accuracy), 4),
        "best_params": grid.best_params_,
        "label_distribution": y.value_counts().to_dict(),
        "classification_report": classification_report(y_test, predictions, output_dict=True),
        "confusion_matrix": confusion_matrix(y_test, predictions, labels=["LOW", "MEDIUM", "HIGH"]).tolist(),
        "labels": ["LOW", "MEDIUM", "HIGH"],
    }
    return best_model, metrics


# 5. 모델 / 평가 결과 저장

def save_outputs(model: Pipeline, metrics: dict, feature_df: pd.DataFrame, output_dir: Path) -> None:
    """학습된 모델, 평가 지표, feature 테이블을 파일로 저장한다."""

    output_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, output_dir / "budget_risk_random_forest.pkl")
    (output_dir / "budget_risk_metrics.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    feature_df.to_csv(output_dir / "budget_risk_features.csv", index=False, encoding="utf-8-sig")


# 6. CLI 실행 옵션

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="예산 초과 위험도 모델 학습")
    parser.add_argument("--seed-dir", default="seed", help="CSV seed 폴더")
    parser.add_argument("--output-dir", default="data/models", help="모델/평가 결과 저장 폴더")
    return parser.parse_args()


# 7. 실행 흐름

def main() -> None:
    args = parse_args()
    seed_dir = Path(args.seed_dir)
    output_dir = Path(args.output_dir)

    data = load_seed(seed_dir)
    feature_df = build_features(data)
    model, metrics = train_model(feature_df)
    save_outputs(model, metrics, feature_df, output_dir)

    print("Budget risk model training complete")
    print(f"rows={metrics['row_count']} train={metrics['train_count']} test={metrics['test_count']}")
    print(f"accuracy={metrics['accuracy']:.4f}")
    print(f"best_params={metrics['best_params']}")
    print(f"label_distribution={metrics['label_distribution']}")
    print(f"model_path={output_dir / 'budget_risk_random_forest.pkl'}")
    print(f"metrics_path={output_dir / 'budget_risk_metrics.json'}")


if __name__ == "__main__":
    main()
