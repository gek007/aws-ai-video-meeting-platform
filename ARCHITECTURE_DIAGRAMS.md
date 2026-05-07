# AI Meeting Intelligence Platform Diagrams

These diagrams show the intended steady-state architecture. The current codebase already implements the queue and persistence scaffolding, plus real `Amazon Transcribe` submission and `Amazon SES` delivery adapters, but `Bedrock`, real media conversion, `OpenSearch`, and true async transcription completion are still pending.

## Architecture Overview

```mermaid
flowchart LR
classDef service fill:#dbeafe,stroke:#5b8def,color:#1f2937,stroke-width:1px;
classDef aws fill:#e8f5e9,stroke:#7cb342,color:#1f2937,stroke-width:1px;
classDef db fill:#ffe8cc,stroke:#d08c60,color:#1f2937,stroke-width:1px;
classDef objectstore fill:#fff1b8,stroke:#c9a227,color:#1f2937,stroke-width:1px;
classDef queue fill:#fff3e0,stroke:#d4a373,color:#1f2937,stroke-width:1px;
classDef external fill:#f3e8ff,stroke:#9b8ad6,color:#1f2937,stroke-width:1px;

A[Meeting Source / UI / Connector] --> B[S3 Raw Video Bucket]
B --> C[EventBridge]
C --> D["Lambda: ingestion-service<br/>- Process: create meeting, video_item, processing_job metadata<br/>- Output: send message to media-processing SQS"]
D --> E[(Aurora PostgreSQL)]
D --> F[SQS: media-processing]

F --> G["Lambda: media-service<br/>- Process: convert video to normalized audio, update media state<br/>- Output: send message to transcription SQS"]
G --> E
G --> H[S3 Audio Bucket]
G --> I[SQS: transcription]

I --> J["Lambda: transcription-service<br/>- Process: start transcription, store transcript reference<br/>- Output: send message to ai-enrichment SQS"]
J --> K[Amazon Transcribe]
J --> E
J --> L[S3 Transcript Bucket]
J --> M[SQS: ai-enrichment]

M --> N["Lambda: ai-enrichment-service<br/>- Process: summarize, extract topics/decisions/action items, generate embeddings<br/>- Output: publish meeting intelligence to SNS"]
N --> O[Amazon Bedrock]
N --> E
N --> P[(OpenSearch Vector Index)]
N --> ZA[SNS: meeting-intelligence-topic]
ZA --> Q[SQS: task-creation]
ZA --> R[SQS: notifications]

Y["Lambda: search-query-service / chat-rag-service<br/>- Process: search related meetings, answer meeting questions with RAG<br/>- Output: grounded response with citations"] --> P
Y --> E
Y --> O

Q --> S["Lambda: task-orchestrator-service<br/>- Process: map action items to provider-ready task requests<br/>- Output: call integration provider and persist external task result"]
S --> T[Jira / GitHub / Linear / Asana]
S --> E

R --> U["Lambda: notification-service<br/>- Process: render template and deliver notification<br/>- Output: email / Slack / Teams message"]
U --> V[SES / Slack / Teams]
U --> E

AA[EventBridge Scheduler] --> W["Lambda: status-observer-service<br/>- Process: poll external task status and detect changes<br/>- Output: update state and push notification event"]
W --> T
W --> E
W --> R

class D,G,J,N,Y,S,U,W service;
class C,K,O,P,ZA aws;
class E db;
class B,H,L objectstore;
class F,I,M,Q,R queue;
class T,V external;
```

## Video Processing Flow

```mermaid
flowchart TD
classDef service fill:#dbeafe,stroke:#5b8def,color:#1f2937,stroke-width:1px;
classDef aws fill:#e8f5e9,stroke:#7cb342,color:#1f2937,stroke-width:1px;
classDef db fill:#ffe8cc,stroke:#d08c60,color:#1f2937,stroke-width:1px;
classDef objectstore fill:#fff1b8,stroke:#c9a227,color:#1f2937,stroke-width:1px;
classDef queue fill:#fff3e0,stroke:#d4a373,color:#1f2937,stroke-width:1px;
classDef external fill:#f3e8ff,stroke:#9b8ad6,color:#1f2937,stroke-width:1px;

A["Meeting Upload / Connector"] --> B["S3 Raw Video Bucket"]
B --> C["EventBridge"]
C --> D["Lambda: ingestion-service<br/>- Process: create metadata records<br/>- Output: send message to media-processing SQS"]
D --> E["Aurora PostgreSQL<br/>(meetings + video_items + processing_jobs)"]
D --> F["SQS: media-processing"]

F --> G["Lambda: media-service<br/>- Process: convert video to audio, update media state<br/>- Output: send message to transcription SQS"]
G --> H["S3 Audio Bucket"]
G --> E
G --> I["SQS: transcription"]

I --> J["Lambda: transcription-service<br/>- Process: create transcript, store transcript reference<br/>- Output: send message to ai-enrichment SQS"]
J --> K["Amazon Transcribe"]
J --> L["S3 Transcript Bucket"]
J --> E
J --> M["SQS: ai-enrichment"]

M --> N["Lambda: ai-enrichment-service<br/>- Process: summarize, extract action items, topics, decisions<br/>- Output: publish meeting intelligence to SNS"]
N --> O["Amazon Bedrock"]
N --> P["OpenSearch Vector Index"]
N --> ZA["SNS: meeting-intelligence-topic"]
N --> E
ZA --> Q["SQS: task-creation"]
ZA --> R["SQS: notifications"]
Q --> S["Lambda: task-orchestrator-service<br/>- Process: prepare external task request and persist external result"]
R --> T["Lambda: notification-service<br/>- Process: deliver participant notification<br/>- Output: email / Slack / Teams message"]

class D,G,J,N,S,T service;
class C,K,O,P,ZA aws;
class E db;
class B,H,L objectstore;
class F,I,M,Q,R queue;
```

## Query, Chat, And Observation Flows

```mermaid
flowchart LR
classDef service fill:#dbeafe,stroke:#5b8def,color:#1f2937,stroke-width:1px;
classDef aws fill:#e8f5e9,stroke:#7cb342,color:#1f2937,stroke-width:1px;
classDef db fill:#ffe8cc,stroke:#d08c60,color:#1f2937,stroke-width:1px;
classDef objectstore fill:#fff1b8,stroke:#c9a227,color:#1f2937,stroke-width:1px;
classDef queue fill:#fff3e0,stroke:#d4a373,color:#1f2937,stroke-width:1px;
classDef external fill:#f3e8ff,stroke:#9b8ad6,color:#1f2937,stroke-width:1px;

A[User / API Client] --> B["Lambda: search-query-service<br/>- Process: search meetings, summaries, action items, related content<br/>- Output: filtered search results"]
B --> C[(Aurora PostgreSQL)]
B --> D[(OpenSearch Vector Index)]

A --> E["Lambda: chat-rag-service<br/>- Process: retrieve transcript chunks and artifacts, build grounded answer<br/>- Output: answer with citations"]
E --> C
E --> D
E --> F[Amazon Bedrock]

G[EventBridge Scheduler] --> H["Lambda: status-observer-service<br/>- Process: poll external task systems, detect status changes<br/>- Output: update state and send notification event"]
H --> C
H --> I[SQS: notifications]
H --> J[Jira / GitHub / Linear / Asana]

I --> K["Lambda: notification-service<br/>- Process: deliver user notification<br/>- Output: email / Slack / Teams message"]
K --> L[SES / Slack / Teams]
K --> C

class B,E,H,K service;
class F,G aws;
class C db;
class D objectstore;
class I queue;
class J,L external;
```
