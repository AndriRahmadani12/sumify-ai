# ERD — Meeting Summarizer Database

Entity Relationship Diagram untuk skema database Meeting Summarizer.
Diagram di bawah ini otomatis ter-render di VSCode (extension Markdown Preview Mermaid)
maupun di GitHub.

> Catatan: field tabel `users` dan struktur kolom JSON (`segments`, `key_points`,
> `action_items`, `decisions`) masih asumsi dari diagram arsitektur. Konfirmasi ke Ndri
> (pemegang repositories/query) sebelum dianggap final.

```mermaid
erDiagram
    USERS ||--o{ MEETINGS : "punya"
    MEETINGS ||--|| TRANSCRIPTIONS : "menghasilkan"
    MEETINGS ||--|| SUMMARIES : "menghasilkan"
    MEETINGS ||--o{ PROCESSING_JOBS : "ditrack oleh"
    PDF_TEMPLATES ||--o{ SUMMARIES : "dipakai"

    USERS {
        uuid id PK
        string email
        string password_hash
        string name
        timestamp created_at
        timestamp updated_at
    }
    MEETINGS {
        uuid id PK
        uuid user_id FK
        string title
        string description
        string language
        string storage_path
        enum status
        string pdf_url
        timestamp created_at
        timestamp updated_at
    }
    TRANSCRIPTIONS {
        uuid id PK
        uuid meeting_id FK
        text full_text
        jsonb segments
        string language
        timestamp created_at
    }
    SUMMARIES {
        uuid id PK
        uuid meeting_id FK
        uuid template_id FK
        text summary
        jsonb key_points
        jsonb action_items
        jsonb decisions
        timestamp created_at
    }
    PROCESSING_JOBS {
        uuid id PK
        uuid meeting_id FK
        enum job_type
        enum status
        string celery_task_id
        text error
        timestamp created_at
        timestamp updated_at
    }
    PDF_TEMPLATES {
        uuid id PK
        string name
        text html_content
        boolean is_active
        timestamp created_at
    }
```

## Ringkasan relasi

|Dari           |Ke               |Jenis|Arti                                                           |
|---------------|-----------------|-----|---------------------------------------------------------------|
|`users`        |`meetings`       |1 : N|satu user punya banyak meeting                                 |
|`meetings`     |`transcriptions` |1 : 1|satu meeting punya satu transkrip                              |
|`meetings`     |`summaries`      |1 : 1|satu meeting punya satu ringkasan                              |
|`meetings`     |`processing_jobs`|1 : N|satu meeting bisa punya banyak job (transcribe, summarize, pdf)|
|`pdf_templates`|`summaries`      |1 : N|satu template dipakai banyak ringkasan                         |

## Alur status `meetings.status`

```
UPLOADED → TRANSCRIBING → SUMMARIZING → GENERATING_PDF → COMPLETED
                                  ↘ (jika gagal di tahap mana pun) ↘ FAILED
```