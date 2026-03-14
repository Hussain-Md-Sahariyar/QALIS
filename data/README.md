# QALIS Data Directory

This directory contains all empirical data collected during the QALIS study
(October–December 2024) across four case systems (S1–S4).

## Structure

```
data/
├── raw/                         
│   ├── S1_Customer_Support_Chatbot/
│   │   ├── metric_snapshots/    
│   │   ├── query_logs/          
│   │   ├── embeddings/           
│   │   ├── annotation_samples/ 
│   │   └── incident_logs/       
│   ├── S2_AI_Code_Assistant_IDE_Plugin/
│   ├── S3_Document_Summarization_and_QA/
│   └── S4_Medical_Triage_Assistant/
├── annotations/                 
│   ├── FC4_factual_precision/    
│   ├── TI2_explanation_faithfulness/ 
│   └── TI3_user_interpretability/    
├── perturbation_tests/        
│   ├── S1/ S2/ S3/ S4/
│   │   ├── typographical_perturbations.csv  
│   │   ├── paraphrase_pairs.csv            
│   │   ├── ood_detection_samples.csv       
│   │   ├── ro1_sensitivity_summary.json
│   │   ├── ro3_ood_summary.json
│   │   └── ro4_invariance_summary.json
├── processed/                   
│   ├── aggregated/              
│   ├── correlations/            
│   ├── longitudinal/            
│   ├── eval_sets/               
│   └── data_dictionary.json     
└── README.md                   
```

## Key Statistics
- **Total observations**: 3,400 quality assessments across S1–S4
- **Study period**: 2024-10-01 to 2024-12-31 (92 days)
- **Query/response pairs**: 50,000 per system (200,000 total)
- **Embedding vectors**: 512-dim float32
- **Human annotations**: 800 (FC-4) + 500 (TI-2) + 1,200 (TI-3) = 2,500 items
- **Perturbation tests**: 5,000 typo + 4,000 paraphrase + 3,000 OOD = 12,000 total

## Large File Note
The `embeddings/` directories contain `.npy` files. These are
excluded from the patch zip but included in the main repository archive parts.
See `configs/embedding_config.yaml` for loading instructions.
