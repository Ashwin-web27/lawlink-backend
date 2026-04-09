# Dataset - Indian Education Law Documents

This directory contains the comprehensive legal document database for the Indian Education Law Chatbot.

## 📁 Directory Structure

```
dataset/
├── legal-documents/         # Original legal documents (source materials)
├── training-data/          # Processed data for training and inference
├── vector-database/        # Vector embeddings and search indices
├── processed-data/         # Cleaned and structured data
├── models/                # Trained models and configurations
└── utils/                 # Data processing scripts and utilities
```

## 📚 Legal Documents

### `/legal-documents/`

Contains original legal documents organized by type:

#### `/acts/` - Education Acts and Legislation
- **Right to Education Act, 2009** (`rte_2009.pdf`)
- **University Grants Commission Act, 1956** (`ugc_act_1956.pdf`)
- **All India Council for Technical Education Act, 1987** (`aicte_act_1987.pdf`)
- **National Council for Teacher Education Act, 1993** (`ncte_act_1993.pdf`)
- **Central Universities Act, 2009** (`central_universities_act_2009.pdf`)

#### `/rules/` - Rules and Regulations
- **UGC Regulations** (various years)
  - Minimum Qualifications for Appointment of Teachers (`ugc_min_qualifications.pdf`)
  - Regulations on Curbing the Menace of Ragging (`ugc_anti_ragging.pdf`)
  - Credit Framework for Online Learning Courses (`ugc_credit_framework.pdf`)
- **CBSE Rules and Regulations**
  - Examination Bye-Laws (`cbse_exam_bylaws.pdf`)
  - Affiliation Bye-Laws (`cbse_affiliation.pdf`)
- **State Education Rules** (by state)

#### `/judgments/` - Court Judgments and Orders
- **Supreme Court Cases**
  - T.M.A. Pai Foundation case (Private education rights)
  - Ashoka Kumar Thakur case (Reservation in higher education)
  - Society for Unaided Private Schools case (Fee regulation)
- **High Court Judgments** (organized by High Court)
- **Tribunal Decisions**

#### `/circulars/` - Government Circulars and Notifications
- **Ministry of Education Circulars**
- **UGC Circulars**
- **CBSE Notifications**
- **State Government Notifications**

#### `/guidelines/` - Policy Guidelines
- **National Education Policy 2020** (`nep_2020.pdf`)
- **UGC Guidelines** (various topics)
- **CBSE Guidelines**
- **COVID-19 Education Guidelines**

## 🔄 Training Data

### `/training-data/`

Processed versions of legal documents for machine learning:

#### `/raw-text/`
- Text extracted from PDFs and documents
- Organized by source document
- Maintains original structure and formatting

#### `/processed-chunks/`
- Documents split into semantically meaningful chunks
- Optimized for retrieval and context windows
- Preserves legal citations and references

#### `/embeddings/`
- Vector embeddings for semantic search
- Generated using appropriate embedding models
- Indexed for fast retrieval

#### `/qa-pairs/`
- Curated question-answer pairs
- Legal scenarios and responses
- Training data for fine-tuning

## 🗃️ Vector Database

### `/vector-database/`
- Vector indices for semantic search
- Metadata mappings
- Search optimization files
- Backup and version control

## 📊 Processed Data

### `/processed-data/`
- Cleaned and structured legal text
- Citation networks and relationships
- Categorized by legal topics
- Standardized formats

## 🤖 Models

### `/models/`
- Trained model checkpoints
- Configuration files
- Model evaluation metrics
- Version history

## 🛠️ Utilities

### `/utils/`
- Data processing scripts
- Text extraction tools
- Vector generation utilities
- Validation and quality checks

## 📋 Data Processing Pipeline

1. **Document Collection**
   - Gather official legal documents
   - Verify authenticity and sources
   - Maintain version control

2. **Text Extraction**
   - Extract text from PDFs and images
   - Preserve formatting and structure
   - Handle legal citations properly

3. **Text Processing**
   - Clean and normalize text
   - Split into semantic chunks
   - Maintain legal context

4. **Vector Generation**
   - Generate embeddings for semantic search
   - Create searchable indices
   - Optimize for retrieval performance

5. **Quality Assurance**
   - Validate extracted content
   - Check citation accuracy
   - Test retrieval quality

## 🎯 Document Naming Convention

### Files should follow this pattern:
```
{category}_{subcategory}_{year}_{version}.{extension}

Examples:
- act_rte_2009_original.pdf
- judgment_sc_tma_pai_2002.pdf
- circular_moe_covid_2020_v2.pdf
- guideline_ugc_choice_based_2021.pdf
```

### Metadata Format:
Each document should have accompanying metadata:
```json
{
  "document_id": "act_rte_2009_original",
  "title": "The Right of Children to Free and Compulsory Education Act, 2009",
  "category": "act",
  "subcategory": "education_rights",
  "year": 2009,
  "authority": "Parliament of India",
  "status": "active",
  "last_updated": "2009-08-26",
  "source_url": "https://official-source.gov.in",
  "language": "english",
  "pages": 27,
  "sections": 38,
  "key_topics": ["right_to_education", "compulsory_education", "quality_norms"],
  "citations": ["Article 21A", "Fundamental Rights"],
  "amendments": []
}
```

## ✅ Quality Standards

### Document Verification
- All documents must be from official government sources
- Cross-reference with official websites
- Maintain chain of custody for document versions

### Text Quality
- OCR accuracy > 99%
- Proper preservation of legal citations
- Consistent formatting across documents

### Legal Accuracy
- Verify current legal status
- Note any amendments or superseded provisions
- Include effective dates and jurisdictions

## 🔐 Legal Compliance

### Copyright and Usage
- All documents are public domain or officially released
- Proper attribution to original sources
- Compliance with government open data policies

### Data Sensitivity
- No personal information in legal judgments
- Anonymized case studies where required
- Compliance with data protection regulations

## 📈 Updates and Maintenance

### Regular Updates
- Monthly scan for new regulations and circulars
- Quarterly review of judgments and policy changes
- Annual comprehensive dataset review

### Version Control
- Semantic versioning for dataset releases
- Change logs for all updates
- Backup and rollback procedures

## 🤝 Contributing Legal Documents

### Submission Guidelines
1. Ensure document is from official source
2. Provide complete metadata
3. Verify legal accuracy and current status
4. Follow naming conventions
5. Include source verification

### Review Process
1. Initial screening for authenticity
2. Legal accuracy verification
3. Technical processing validation
4. Integration testing
5. Final approval and integration

## ⚖️ Legal Notice

This dataset is compiled from publicly available legal documents from official government sources. While every effort is made to ensure accuracy and completeness, users should always verify information with original official sources for legal purposes.

**Disclaimer**: This dataset is for educational and informational purposes only. It does not constitute legal advice and should not be relied upon for legal decisions.