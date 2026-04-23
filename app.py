from flask import Flask, request, render_template
import numpy as np
import pandas as pd
import joblib
from tensorflow.keras.models import load_model

app = Flask(__name__)

# Load saved components
model = load_model("models/dnn_attention_model.h5")
scaler = joblib.load("models/scaler.pkl")
label_encoder = joblib.load("models/label_encoder.pkl")

@app.route('/')
def home():
    return render_template('index.html')


# -------------------------
# EXISTING PREDICTION MODE
# -------------------------
@app.route('/predict', methods=['POST'])
def predict():
    try:
        file = request.files['file']
        df = pd.read_csv(file)

        if 'Label' in df.columns:
            df = df.drop('Label', axis=1)

        df_scaled = scaler.transform(df)

        preds = model.predict(df_scaled)

        class_indices = np.argmax(preds, axis=1)
        labels = label_encoder.inverse_transform(class_indices)

        from collections import Counter
        count = Counter(labels)

        final_label = count.most_common(1)[0][0]

        total = len(labels)
        confidence = (count[final_label] / total) * 100

        return render_template(
            'result.html',
            final_label=final_label,
            confidence=round(confidence, 2)
        )

    except Exception as e:
        return str(e)


# -------------------------
# NEW VERIFICATION FEATURE
# -------------------------
@app.route('/verify', methods=['POST'])
def verify():
    try:
        file = request.files['file']
        df = pd.read_csv(file)

        if 'Label' not in df.columns:
            return "Verification requires a dataset WITH a Label column."

        y_true = df['Label']
        X = df.drop('Label', axis=1)

        X_scaled = scaler.transform(X)

        preds = model.predict(X_scaled)
        class_indices = np.argmax(preds, axis=1)
        pred_labels = label_encoder.inverse_transform(class_indices)

        from sklearn.metrics import accuracy_score

        accuracy = accuracy_score(y_true, pred_labels)

        comparison = pd.DataFrame({
            "Actual": y_true,
            "Predicted": pred_labels
        })

        matches = (comparison["Actual"] == comparison["Predicted"]).sum()

        return render_template(
            "verify.html",
            accuracy=round(accuracy * 100, 2),
            matches=matches,
            total=len(comparison),
            table=comparison.head(20).to_html(classes="table table-striped")
        )

    except Exception as e:
        return str(e)


if __name__ == "__main__":
    app.run(debug=True)