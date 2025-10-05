import pandas as pd
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    Trainer,
    TrainingArguments,
    BertTokenizer
)
from datasets import Dataset
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
import mlflow
import numpy as np
import torch
import random

# Set seed to make random operations reproducible across runs
def set_seed(seed_value=42):
    random.seed(seed_value)
    np.random.seed(seed_value)
    torch.manual_seed(seed_value)
    torch.cuda.manual_seed(seed_value)
    torch.cuda.manual_seed_all(seed_value)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
SEED = 42
set_seed(SEED)

# Load dataset
# train
df_train = pd.read_csv("data/data_train_judol.csv")
y_train = df_train['label']
X_train = df_train.drop(columns=['label'])
# valid
df_valid = pd.read_csv("data/data_valid_judol.csv")
y_valid = df_valid['label']
X_valid = df_valid.drop(columns=['label'])
# test
df_test = pd.read_csv("data/data_test_judol.csv")
y_test = df_test['label']
X_test = df_test.drop(columns=['label'])

# get tokenizer with fallback
def get_tokenizer(model_name):
    try:
        # most model work with this
        return AutoTokenizer.from_pretrained(model_name)
    except:
        # but IndoBert need to use BertTokenizer
        return BertTokenizer.from_pretrained(model_name)
    
def tokenize_text(tokenizer, data):
    """
    max token the tokenizer will generate is 512 and if length of token from text is more than that
    it will get truncated, default is like last truncate, and if length of token is less than 512
    it will fill with padding [PAD], this token doesn't mean anything, just to make the length of token
    for each data is uniform (512)
    """
    return tokenizer(data['text'], max_length=512, truncation=True, padding='max_length')

def compute_metrics(eval_pred):
    """
    Create custom evaluation metric to be used in Trainer
    """
    logits, labels = eval_pred # destructor value
    preds = logits.argmax(axis=1) # get index of max value in logits
    """
    for example, 2 logits data of binary classification is [[1.2, 2.3], [1.4, 0.5]]
    then the output from above code is preds = [1, 0] 
    because max value for each logits data is in index 1 for data 1 and index 0 for data 2 
    """

    precision, recall, f1, _ = precision_recall_fscore_support(
        labels, preds, average='binary', zero_division=0
    )
    acc = accuracy_score(labels, preds)
    
    return {
        'accuracy': acc,
        'precision': precision,
        'recall': recall,
        'f1': f1
    }

models_to_train = {
    "distilbert/distilroberta-base": "distilroberta",
    "indobenchmark/indobert-lite-base-p2": "indobert-lite"
}

# loop for each model
for model_name, model_tag in models_to_train.items():
    print(f"\n===== Training {model_tag} =====")
    # get appropriate tokenizer
    tokenizer = get_tokenizer(model_name)

    # create dataset
    train_dataset = Dataset.from_dict({"text": X_train['clean_comment'], "label": y_train})
    valid_dataset = Dataset.from_dict({"text": X_valid['clean_comment'], "label": y_valid})
    test_dataset = Dataset.from_dict({"text": X_test['clean_comment'], "label": y_test})

    # tokenize dataset
    train_dataset = train_dataset.map(lambda data: tokenize_text(tokenizer, data), batched=True)
    valid_dataset = valid_dataset.map(lambda data: tokenize_text(tokenizer, data), batched=True)
    test_dataset = test_dataset.map(lambda data: tokenize_text(tokenizer, data), batched=True)

    # set format to torch
    train_dataset.set_format(type="torch", columns=["input_ids", "attention_mask", "label"])
    valid_dataset.set_format(type="torch", columns=["input_ids", "attention_mask", "label"])
    test_dataset.set_format(type="torch", columns=["input_ids", "attention_mask", "label"])

    # load model
    """
    parameter num_labels 1 default setting is for regression where the loss function used is MSE
    num_labels > 1 default setting is for classification where the loss function used is Cross-Entropy
    """
    model = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=2).to("cuda")

    # define hyperparameter
    learning_rate = 2e-5 # how big the gradient impact when updating parameter model
    batch_size = 8 # number of mini batch data, number of data used for training for each step
    num_epochs = 5 # number of iteration
    output_dir = f"./results/{model_tag}"

    # create training arguments
    training_args = TrainingArguments(
        output_dir=output_dir,
        eval_strategy="epoch",
        save_strategy="epoch",
        per_device_train_batch_size=batch_size,
        per_device_eval_batch_size=batch_size,
        num_train_epochs=num_epochs,
        learning_rate=learning_rate,
        load_best_model_at_end=True, # save best model based on accuracy
        metric_for_best_model="accuracy", # use accuracy because our data is balanced, prefer f1-score if your data is imbalance
        greater_is_better=True,
        logging_dir=f"{output_dir}/logs",
        save_total_limit=1, # save just one model
    )

    # create trainer to select the model, training arguments, data, and metric used when training and evaluation on data validation
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=valid_dataset,
        compute_metrics=compute_metrics
    )

    # start mlflow logging
    with mlflow.start_run(run_name=model_tag):
        # log hyperparameter
        mlflow.log_param("model_name", model_name)
        mlflow.log_param("batch_size", batch_size)
        mlflow.log_param("learning_rate", learning_rate)
        mlflow.log_param("epochs", num_epochs)

        # train the model
        trainer.train()

        # model evaluation on test data
        predictions = trainer.predict(test_dataset)
        preds = np.argmax(predictions.predictions, axis=1)
        labels = predictions.label_ids

        # get metric evaluation from test data
        acc = accuracy_score(labels, preds)
        precision, recall, f1, _ = precision_recall_fscore_support(labels, preds, average='binary', zero_division=0)

        # log evaluation metric
        mlflow.log_metric("test_accuracy", acc)
        mlflow.log_metric("test_precision", precision)
        mlflow.log_metric("test_recall", recall)
        mlflow.log_metric("test_f1", f1)

        # save model to mlflow
        mlflow.pytorch.log_model(trainer.model, artifact_path="model")

        # save prediction
        df_result = pd.DataFrame({
            "text": X_test['clean_comment'].tolist(),
            "label": labels,
            "prediction": preds
        })

        # save to csv and log into mlflow
        result_path = f"data/prediction/preds_{model_tag}.csv"
        df_result.to_csv(result_path, index=False)
        mlflow.log_artifacts(result_path)

        print(f"Training DONE for model : {model_tag} | Test Accuracy: {acc:.4f}, F1: {f1:.4f}")