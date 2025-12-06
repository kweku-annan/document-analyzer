# 📄 AI Document Analyzer

An intelligent document processing service that automatically extracts text from PDF and DOCX files, analyzes them using AI, and extracts key metadata like document type, summaries, and relevant information.

## 🌟 Features

- **Document Upload**: Support for PDF and DOCX files (up to 5MB)
- **Text Extraction**: Automatic text extraction from uploaded documents
- **AI-Powered Analysis**: 
  - Concise document summaries
  - Automatic document type detection (invoice, CV, report, letter, etc.)
  - Smart metadata extraction (dates, amounts, names, etc.)
- **RESTful API**: Clean and well-documented API endpoints
- **Database Storage**: Persistent storage of documents and analysis results
- **Interactive Documentation**: Auto-generated API docs with Swagger UI

## 🏗️ Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│   FastAPI App   │
└────────┬────────┘
         │
    ┌────┴────┬──────────┬─────────────┐
    ▼         ▼          ▼             ▼
┌─────────┐ ┌──────┐ ┌─────────┐ ┌──────────┐
│ Storage │ │ Text │ │   AI    │ │PostgreSQL│
│ Service │ │Extract│ │Analyzer │ │ Database │
└─────────┘ └──────┘ └─────────┘ └──────────┘
    │           │          │
    ▼           ▼          ▼
┌─────────┐ ┌────────┐ ┌───────────┐
│  Local  │ │PyPDF2  │ │ OpenRouter│
│  Files  │ │python- │ │    API    │
│         │ │  docx  │ │           │
└─────────┘ └────────┘ └───────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- PostgreSQL 12+
- [UV](https://github.com/astral-sh/uv) package manager
- OpenRouter API key ([Get one here](https://openrouter.ai/))

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd document-analyzer
   ```

2. **Install UV** (if not already installed)
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

3. **Install dependencies**
   ```bash
   uv sync
   ```

4. **Set up PostgreSQL database**
   ```bash
   # Connect to PostgreSQL
   psql -U postgres
   
   # Create database
   CREATE DATABASE document_analyzer;
   
   # Exit
   \q
   ```

5. **Configure environment variables**
   
   Create a `.env` file in the project root:
   ```env
   # Database
   DATABASE_URL=postgresql://username:password@localhost:5432/document_analyzer
   
   # Storage
   UPLOAD_DIR=uploads
   MAX_FILE_SIZE=5242880
   
   # OpenRouter API
   OPENROUTER_API_KEY=your_api_key_here
   OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
   OPENROUTER_MODEL=openai/gpt-4o-mini
   
   # App
   APP_NAME=Document Analyzer API
   DEBUG=True
   ```

6. **Initialize the database**
   ```bash
   uv run python init_db.py
   ```

7. **Run the application**
   ```bash
   uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

8. **Access the application**
   - API: http://localhost:8000
   - Interactive docs: http://localhost:8000/docs
   - Alternative docs: http://localhost:8000/redoc

## 📚 API Documentation

### Endpoints

#### 1. Health Check
```http
GET /
```
Check if the API is running.

**Response:**
```json
{
  "message": "Document Analyzer API is running",
  "version": "1.0.0"
}
```

---

#### 2. Upload Document
```http
POST /documents/upload
```
Upload a PDF or DOCX file for processing.

**Request:**
- Content-Type: `multipart/form-data`
- Body: `file` (PDF or DOCX, max 5MB)

**Response:** (201 Created)
```json
{
  "id": 1,
  "filename": "invoice.pdf",
  "file_size": 45678,
  "file_type": "pdf",
  "message": "Document uploaded successfully. Use /documents/{id}/analyze to analyze it."
}
```

**Errors:**
- `400 Bad Request`: Invalid file type or empty file
- `413 Payload Too Large`: File exceeds 5MB

---

#### 3. Analyze Document
```http
POST /documents/{document_id}/analyze
```
Analyze a document using AI to extract summary, type, and metadata.

**Response:** (200 OK)
```json
{
  "id": 1,
  "summary": "This is an invoice from ABC Company for services rendered in January 2024, totaling $1,234.56.",
  "document_type": "invoice",
  "metadata": {
    "invoice_number": "INV-2024-001",
    "date": "2024-01-15",
    "total_amount": "$1,234.56",
    "vendor": "ABC Company",
    "customer": "XYZ Corp"
  },
  "is_analyzed": "completed"
}
```

**Supported Document Types:**
- Invoice
- CV/Resume
- Report
- Letter
- Contract
- Receipt
- Form
- Other

**Errors:**
- `404 Not Found`: Document doesn't exist
- `400 Bad Request`: No extracted text available
- `500 Internal Server Error`: Analysis failed (check API key)

---

#### 4. Get Document Details
```http
GET /documents/{document_id}
```
Retrieve complete information about a document.

**Response:** (200 OK)
```json
{
  "id": 1,
  "filename": "invoice.pdf",
  "file_size": 45678,
  "file_type": "pdf",
  "file_path": "uploads/invoice_20241206_143022.pdf",
  "extracted_text": "Full extracted text...",
  "summary": "AI-generated summary...",
  "document_type": "invoice",
  "metadata": {
    "invoice_number": "INV-2024-001",
    "date": "2024-01-15"
  },
  "is_analyzed": "completed",
  "analysis_error": null,
  "created_at": "2024-12-06T14:30:22.123456",
  "updated_at": "2024-12-06T14:31:15.789012"
}
```

---

#### 5. List Documents
```http
GET /documents?skip=0&limit=10
```
List all documents with pagination.

**Query Parameters:**
- `skip` (optional, default: 0): Number of documents to skip
- `limit` (optional, default: 10): Maximum documents to return

**Response:** (200 OK)
```json
[
  {
    "id": 1,
    "filename": "invoice.pdf",
    "file_type": "pdf",
    "is_analyzed": "completed",
    ...
  },
  {
    "id": 2,
    "filename": "resume.docx",
    "file_type": "docx",
    "is_analyzed": "pending",
    ...
  }
]
```

## 🔧 Usage Examples

### Using cURL

**Upload a document:**
```bash
curl -X POST "http://localhost:8000/documents/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@invoice.pdf"
```

**Analyze a document:**
```bash
curl -X POST "http://localhost:8000/documents/1/analyze"
```

**Get document details:**
```bash
curl -X GET "http://localhost:8000/documents/1"
```

**List all documents:**
```bash
curl -X GET "http://localhost:8000/documents?limit=20"
```

### Using Python

```python
import requests

# Upload document
with open('invoice.pdf', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/documents/upload',
        files={'file': f}
    )
    document = response.json()
    doc_id = document['id']

# Analyze document
response = requests.post(f'http://localhost:8000/documents/{doc_id}/analyze')
analysis = response.json()

print(f"Summary: {analysis['summary']}")
print(f"Type: {analysis['document_type']}")
print(f"Metadata: {analysis['metadata']}")
```

### Using JavaScript (fetch)

```javascript
// Upload document
const formData = new FormData();
formData.append('file', fileInput.files[0]);

const uploadResponse = await fetch('http://localhost:8000/documents/upload', {
  method: 'POST',
  body: formData
});
const document = await uploadResponse.json();

// Analyze document
const analyzeResponse = await fetch(
  `http://localhost:8000/documents/${document.id}/analyze`,
  { method: 'POST' }
);
const analysis = await analyzeResponse.json();

console.log(analysis);
```

## 🗂️ Project Structure

```
document-analyzer/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application & routes
│   ├── models.py            # SQLAlchemy database models
│   ├── schemas.py           # Pydantic validation schemas
│   ├── database.py          # Database connection & session
│   ├── config.py            # Configuration management
│   └── services/
│       ├── __init__.py
│       ├── storage.py       # File storage service
│       ├── extractor.py     # Text extraction service
│       └── analyzer.py      # AI analysis service
├── uploads/                 # Document storage directory
├── .env                     # Environment variables (not in git)
├── .gitignore
├── init_db.py              # Database initialization script
├── pyproject.toml          # UV dependencies
└── README.md
```

## 🔐 Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DATABASE_URL` | PostgreSQL connection string | - | ✅ |
| `UPLOAD_DIR` | Directory for file storage | `uploads` | ❌ |
| `MAX_FILE_SIZE` | Maximum file size in bytes | `5242880` (5MB) | ❌ |
| `OPENROUTER_API_KEY` | OpenRouter API key | - | ✅ |
| `OPENROUTER_BASE_URL` | OpenRouter API base URL | `https://openrouter.ai/api/v1` | ❌ |
| `OPENROUTER_MODEL` | AI model to use | `openai/gpt-4o-mini` | ❌ |
| `APP_NAME` | Application name | `Document Analyzer API` | ❌ |
| `DEBUG` | Enable debug mode | `True` | ❌ |

## 🧪 Testing

### Manual Testing with Swagger UI

1. Start the server: `uv run uvicorn app.main:app --reload`
2. Open http://localhost:8000/docs
3. Test each endpoint interactively

### Test Flow

1. **Upload** a sample PDF or DOCX file
2. **Verify** the upload response contains document ID
3. **Analyze** the document using the returned ID
4. **Check** the analysis results (summary, type, metadata)
5. **Retrieve** full document details

## 📊 Database Schema

### Documents Table

| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer | Primary key |
| `filename` | String(255) | Original filename |
| `file_path` | String(500) | Storage path |
| `file_size` | Integer | Size in bytes |
| `file_type` | String(50) | File extension (pdf, docx) |
| `extracted_text` | Text | Extracted document text |
| `summary` | Text | AI-generated summary |
| `document_type` | String(100) | Detected document type |
| `metadata` | JSON | Extracted metadata |
| `is_analyzed` | String(20) | Status: pending/completed/failed |
| `analysis_error` | Text | Error message if failed |
| `created_at` | DateTime | Upload timestamp |
| `updated_at` | DateTime | Last update timestamp |

## 🛠️ Technologies Used

- **[FastAPI](https://fastapi.tiangolo.com/)**: Modern web framework
- **[UV](https://github.com/astral-sh/uv)**: Fast Python package manager
- **[SQLAlchemy](https://www.sqlalchemy.org/)**: SQL toolkit and ORM
- **[PostgreSQL](https://www.postgresql.org/)**: Relational database
- **[PyPDF2](https://pypdf2.readthedocs.io/)**: PDF text extraction
- **[python-docx](https://python-docx.readthedocs.io/)**: DOCX text extraction
- **[OpenRouter](https://openrouter.ai/)**: AI model API gateway
- **[Pydantic](https://docs.pydantic.dev/)**: Data validation
- **[HTTPX](https://www.python-httpx.org/)**: Async HTTP client

## 🚧 Future Enhancements

- [ ] Automatic analysis on upload
- [ ] Support for more file formats (images, Excel, etc.)
- [ ] Batch document upload
- [ ] Document search functionality
- [ ] User authentication & authorization
- [ ] S3/Minio cloud storage integration
- [ ] Document deletion endpoint
- [ ] Rate limiting
- [ ] Webhooks for async processing
- [ ] Document versioning
- [ ] Export analysis results (JSON, CSV)

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🐛 Troubleshooting

### Common Issues

**Issue: "Database connection failed"**
- Verify PostgreSQL is running: `sudo systemctl status postgresql`
- Check `DATABASE_URL` in `.env` has correct credentials
- Ensure database exists: `psql -l | grep document_analyzer`

**Issue: "OpenRouter API error"**
- Verify `OPENROUTER_API_KEY` is set in `.env`
- Check API key is valid at https://openrouter.ai/keys
- Ensure you have credits in your OpenRouter account

**Issue: "File upload fails"**
- Check file size is under 5MB
- Verify file type is PDF or DOCX
- Ensure `uploads/` directory exists and is writable

**Issue: "Text extraction fails"**
- For PDFs: Some PDFs are image-based (scanned) and need OCR
- For DOCX: Ensure file is not corrupted
- Check error message in `analysis_error` field

## 📧 Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Contact: [your-email@example.com]

## 🙏 Acknowledgments

- OpenRouter for providing access to multiple AI models
- FastAPI for the excellent web framework
- The open-source community for amazing tools

---

**Built with ❤️ using Python and FastAPI For HNG-13 INTERNSHIP**