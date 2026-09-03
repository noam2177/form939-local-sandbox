import pandas as pd

def clean_csv():
    df = pd.read_csv('logs/benchmark_results.csv')
    # Take the last 20 rows for each model to isolate the final benchmark run
    clean_df = df.groupby('model').tail(20)
    clean_df.to_csv('logs/benchmark_results_clean.csv', index=False)
    print("Cleaned data saved. Rows per model:")
    print(clean_df['model'].value_counts())

if __name__ == '__main__':
    clean_csv()
