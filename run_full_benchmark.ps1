Write-Host "Waiting for model downloads to complete..."
Start-Sleep -Seconds 300

Write-Host "Running benchmark on all 3 local models..."
python src/main.py --input-dir data/synthetic_inputs --gt-csv data/gold/synthetic_ground_truth.csv

Write-Host "Generating dashboard..."
python src/dashboard.py

Write-Host "Combining to Excel..."
python combine_to_excel.py

Write-Host "Copying results to desktop..."
Copy-Item -Path "logs\*" -Destination "C:\Users\noam1\Desktop\סגולי בדיקות לוקאלי\" -Recurse -Force
Copy-Item -Path "C:\Users\noam1\Desktop\סגולי בדיקות לוקאלי\Form939_Combined_Reports.xlsx" -Destination "C:\Users\noam1\Desktop\סגולי בדיקות לוקאלי\Local_Form939_Research.xlsx" -Force

Write-Host "Done"
