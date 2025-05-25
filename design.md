graph TD
    A[Central Core] -->|Aggregates| B[Node 1: GitHub Adapter]
    A -->|Data Sync| C[Node 2: AWS Adapter]
    A ⇥Policy Enforcement| D[Node 3: Azure Adapter]
    E[(S3 Storage)] ⇥Asset Data| A