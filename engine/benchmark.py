import time, psutil, torch
import pandas as pd
from tqdm import tqdm
from transformers import AutoTokenizer, AutoModelForSequenceClassification, BertTokenizer
from torch.utils.data import DataLoader
from datasets import Dataset
import sys, os
import subprocess

# load test dataset
data_test = pd.read_csv("data/data_test_judol.csv")
test_texts = data_test['clean_comment'].tolist()
label = data_test['label'].tolist()
test_dataset = Dataset.from_dict({"text": test_texts, "label": label})

def benchmark(model, tokenizer, dataset, device, batch_size=1):
    """
    benchmark for fine-tuned model
    """
    if device.type == 'cuda':
        torch.cuda.reset_peak_memory_stats()
        torch.cuda.empty_cache()

    model.to(device)
    model.eval()
    dataloader = DataLoader(dataset, batch_size=batch_size)
    total_time = 0

    with torch.no_grad():
        for batch in tqdm(dataloader, desc=f"Inference on {device}"):
            start = time.perf_counter()
            inputs = tokenizer(batch['text'][0], return_tensors='pt', truncation=True, padding=True, max_length=512)
            inputs = {k: v.to(device) for k, v in inputs.items()}
            _ = model(**inputs)
            end = time.perf_counter()
            total_time += (end - start)

    avg_time = total_time / len(dataset)
    if device.type == 'cuda':
        peak_memory = torch.cuda.max_memory_allocated(device) / (1024 ** 2)
    else:
        process = psutil.Process()
        peak_memory = process.memory_info().rss / (1024 ** 2)

    return avg_time, peak_memory

# load model and tokenizer
model_name_indobert = "indobenchmark/indobert-lite-base-p2"
model_name_roberta = "distilbert/distilroberta-base"

model_indobert = AutoModelForSequenceClassification.from_pretrained(model_name_indobert, num_labels=2)
model_indobert.load_state_dict(torch.load("models/best_indobert.pt", weights_only=True))

model_roberta = AutoModelForSequenceClassification.from_pretrained(model_name_roberta, num_labels=2)
model_roberta.load_state_dict(torch.load("models/best_roberta.pt", weights_only=True))

tokenizer_indobert = BertTokenizer.from_pretrained(model_name_indobert)
tokenizer_roberta = AutoTokenizer.from_pretrained(model_name_roberta)

# benchmark fine-tuned model on CPU and GPU
def run_benchmark(batch_size):
    avg_cpu_indobert, mem_cpu_indobert = benchmark(model_indobert, tokenizer_indobert, test_dataset, torch.device("cpu"), batch_size=batch_size)
    avg_cuda_indobert, mem_cuda_indobert = benchmark(model_indobert, tokenizer_indobert, test_dataset, torch.device("cuda"), batch_size=batch_size)
    avg_cpu_roberta, mem_cpu_roberta = benchmark(model_roberta, tokenizer_roberta, test_dataset, torch.device("cpu"), batch_size=batch_size)
    avg_cuda_roberta, mem_cuda_roberta = benchmark(model_roberta, tokenizer_roberta, test_dataset, torch.device("cuda"), batch_size=batch_size)

    print(f"\n===== BENCHMARK RESULTS (Batch Size = {batch_size}) =====")
    print("Model\t\tDevice\tPeak Mem (MB)\tTime/sample (s)")
    print(f"IndoBERT-lite\tCPU\t{mem_cpu_indobert:.2f}\t\t{avg_cpu_indobert:.6f}")
    print(f"IndoBERT-lite\tGPU\t{mem_cuda_indobert:.2f}\t\t{avg_cuda_indobert:.6f}")
    print(f"DistilRoBERTa\tCPU\t{mem_cpu_roberta:.2f}\t\t{avg_cpu_roberta:.6f}")
    print(f"DistilRoBERTa\tGPU\t{mem_cuda_roberta:.2f}\t\t{avg_cuda_roberta:.6f}")

    # add benchmark result
    benchmark_result.extend([
        {
            "model": "IndoBERT-lite",
            "device": "CPU",
            "batch_size": batch_size,
            "peak_mem_mb": mem_cpu_indobert,
            "time_per_sample": avg_cpu_indobert
        },
        {
            "model": "IndoBERT-lite",
            "device": "GPU",
            "batch_size": batch_size,
            "peak_mem_mb": mem_cuda_indobert,
            "time_per_sample": avg_cuda_indobert
        },
        {
            "model": "DistilRoBERTa",
            "device": "CPU",
            "batch_size": batch_size,
            "peak_mem_mb": mem_cpu_roberta,
            "time_per_sample": avg_cpu_roberta
        },
        {
            "model": "DistilRoBERTa",
            "device": "GPU",
            "batch_size": batch_size,
            "peak_mem_mb": mem_cuda_roberta,
            "time_per_sample": avg_cuda_roberta
        }
    ])


if len(sys.argv) > 1 and sys.argv[1] == "--run":
    bz = int(sys.argv[2])
    benchmark_result = []
    run_benchmark(bz)

    df_benchmark = pd.DataFrame(benchmark_result)
    
    # append mode
    df_benchmark.to_csv("data/benchmark_batchsize.csv", mode="a", index=False, header=not os.path.exists("data/benchmark_batchsize.csv"))

# Bagian utama yang menjalankan semua subprocess
elif __name__ == "__main__":
    list_bz = [1, 4, 8, 16, 32, 64, 128]

    for bz in list_bz:
        print(f"\nRunning benchmark for batch size: {bz}")
        subprocess.run([sys.executable, __file__, "--run", str(bz)])