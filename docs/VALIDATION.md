# Validation and interpretation

## Source file checks

The project validates required target and feature fields, target values, missing values, exact duplicates, and class balance. Initial inspection of the included CSV: 1,470 rows × 35 columns; 0 missing cells; 0 exact duplicate rows; target counts: No=1,233 and Yes=237 (16.1% Yes). See `reports/data_validation.json` after training.

## Evaluation protocol

Stratified 80/20 train/holdout split; compare Logistic Regression and Random Forest by stratified five-fold cross-validation on training data. All imputing, scaling, and one-hot encoding happen in an sklearn pipeline. The selected logistic pipeline is sigmoid-calibrated with cross-validation using training data only, then evaluated once on the untouched holdout. Metrics include class-specific precision/recall/F1, balanced accuracy, ROC-AUC, average precision, Brier score, and confusion matrix. Results are written to `reports/`.

This is an internal educational benchmark, not proof of production performance. With 237 positive rows, subgroup metrics and probabilities may be noisy. Random holdout validation does not evaluate future periods or another company. Read metrics in context, especially false positives and false negatives.

## Recorded holdout result

With seed 42 and the eight fields shown in the dashboard, the untouched 294-row holdout produced ROC-AUC 0.802 and average precision 0.574. The screening threshold was selected using training-only nested out-of-fold estimates to target at least 75% recall, choosing the highest precision among eligible thresholds. The chosen threshold was 0.139. On holdout, recall was 0.809 (38 of 47 leavers detected; 9 missed), precision was 0.288 (94 false-positive flags among 132 flagged records), F1 was 0.425, balanced accuracy was 0.714, and Brier score was 0.103. The higher recall comes with many false alarms; the cutoff does not represent certainty. These figures are only for this fictional dataset.

Risk-band labels compare each probability with the training-partition attrition baseline (0.162) and selected review cutoff (0.139). The model report and UI show both reference values. An estimate above the higher boundary is labeled High; between boundaries is Medium; below the lower boundary is Low. The separate screening flag uses only the selected cutoff.

## Explanation

For Logistic Regression, feature contributions are coefficient × encoded feature value, centered around the model intercept, in the base model's log-odds space. The dashboard groups encoded terms back to source fields and averages them across the calibrated ensemble; they are approximate explanations of the base estimators, not an exact decomposition of calibrated probability. A positive contribution pushes the base model score upward relative to its intercept; a negative one pushes it downward. It is neither a causal reason nor a guaranteed intervention. Overtime is not an automatic rule: its learned effect is considered together with all other inputs.
