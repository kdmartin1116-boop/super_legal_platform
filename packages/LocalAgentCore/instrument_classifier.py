"""
InstrumentClassifier - Legal Document Classification System
========================================================

This module provides intelligent classification of legal documents using
machine learning techniques and legal domain expertise. It categorizes
documents by type, purpose, jurisdiction, and other relevant attributes.

Features:
- Document type classification (contracts, agreements, letters, etc.)
- Sub-category identification
- Confidence scoring
- Multi-label classification support
- Legal domain-specific feature extraction
"""

import asyncio
import re
from datetime import datetime
from typing import Dict, List, Optional, Any, Set, Tuple
from collections import Counter
import spacy

from .base import BaseAnalyzer, AnalysisResult, Classification, DocumentType, SeverityLevel
from .exceptions import ClassificationError, ModelError


class InstrumentClassifier(BaseAnalyzer):
    """
    AI-powered legal document classifier
    
    Classifies documents into categories such as:
    - Contracts (service, employment, sales, etc.)
    - Agreements (NDA, partnership, licensing, etc.) 
    - Legal letters (demand, cease & desist, notice, etc.)
    - Court documents (motions, briefs, complaints, etc.)
    - Administrative documents (affidavits, forms, etc.)
    """
    
    VERSION = "1.0.0"
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.nlp = None
        self._classification_rules: Dict[DocumentType, Dict] = {}
        self._legal_patterns: Dict[str, List[str]] = {}
        self._document_signatures: Dict[DocumentType, Set[str]] = {}
    
    def _initialize(self) -> None:
        """Initialize the document classifier"""
        try:
            # Load spaCy model
            model_name = self.config.get("nlp_model", "en_core_web_sm")
            self.nlp = spacy.load(model_name)
        except OSError:
            raise ModelError(f"Failed to load spaCy model: {model_name}")
        
        # Initialize classification rules and patterns
        self._load_classification_rules()
        self._load_legal_patterns()
        self._build_document_signatures()
    
    def _load_classification_rules(self) -> None:
        """Load document classification rules"""
        self._classification_rules = {
            DocumentType.CONTRACT: {
                "keywords": ["agreement", "contract", "hereby", "whereas", "consideration", "parties", "covenant"],
                "phrases": ["this agreement", "enter into", "binding agreement", "terms and conditions"],
                "sections": ["recitals", "definitions", "obligations", "termination", "governing law"],
                "patterns": [r"\bwhereas\b", r"\bnow therefore\b", r"\bconsideration\b"],
                "confidence_threshold": 0.7
            },
            
            DocumentType.AGREEMENT: {
                "keywords": ["agreement", "understand", "acknowledge", "mutual", "parties", "undertake"],
                "phrases": ["mutual agreement", "parties agree", "understanding between"],
                "sections": ["purpose", "scope", "responsibilities", "duration"],
                "patterns": [r"\bmutual\s+agreement\b", r"\bparties\s+agree\b"],
                "confidence_threshold": 0.6
            },
            
            DocumentType.AFFIDAVIT: {
                "keywords": ["affidavit", "sworn", "depose", "oath", "affirm", "swear", "notary"],
                "phrases": ["being duly sworn", "under oath", "swear under penalty"],
                "sections": ["jurat", "verification", "signature"],
                "patterns": [r"\bsworn\s+statement\b", r"\bunder\s+oath\b", r"\bnotary\s+public\b"],
                "confidence_threshold": 0.8
            },
            
            DocumentType.LETTER: {
                "keywords": ["dear", "sincerely", "regards", "correspondence", "letter"],
                "phrases": ["dear sir", "dear madam", "to whom it may concern", "yours sincerely"],
                "sections": ["date", "salutation", "body", "closing", "signature"],
                "patterns": [r"\bdear\s+\w+\b", r"\byours?\s+sincerely\b", r"\bbest\s+regards\b"],
                "confidence_threshold": 0.5
            },
            
            DocumentType.MOTION: {
                "keywords": ["motion", "court", "honorable", "petition", "request", "relief", "plaintiff", "defendant"],
                "phrases": ["respectfully moves", "motion for", "comes now", "honorable court"],
                "sections": ["caption", "introduction", "statement of facts", "argument", "prayer for relief"],
                "patterns": [r"\bmotion\s+for\b", r"\bhonor(able)?\s+court\b", r"\bplaintiff\b", r"\bdefendant\b"],
                "confidence_threshold": 0.8
            },
            
            DocumentType.BRIEF: {
                "keywords": ["brief", "argument", "court", "case", "precedent", "statute", "holding", "reasoning"],
                "phrases": ["statement of the case", "summary of argument", "table of authorities"],
                "sections": ["table of contents", "table of authorities", "statement of facts", "argument", "conclusion"],
                "patterns": [r"\btable\s+of\s+authorities\b", r"\bstatement\s+of\s+the\s+case\b"],
                "confidence_threshold": 0.7
            },
            
            DocumentType.COMPLAINT: {
                "keywords": ["complaint", "plaintiff", "defendant", "jurisdiction", "venue", "cause of action", "damages"],
                "phrases": ["comes now", "cause of action", "prayer for relief", "jury trial demanded"],
                "sections": ["parties", "jurisdiction", "facts", "causes of action", "prayer for relief"],
                "patterns": [r"\bcause\s+of\s+action\b", r"\bprayer\s+for\s+relief\b", r"\bjury\s+trial\b"],
                "confidence_threshold": 0.8
            }
        }
    
    def _load_legal_patterns(self) -> None:
        """Load legal language patterns for classification"""
        self._legal_patterns = {
            "contract_formation": [
                "in consideration of", "mutual covenants", "binding agreement", 
                "valid consideration", "meeting of minds"
            ],
            "obligations": [
                "shall perform", "agrees to", "undertakes to", "covenants to",
                "obligated to", "responsible for", "duty to"
            ],
            "termination": [
                "terminate this agreement", "expiration of", "breach of contract",
                "material breach", "cure period", "notice of termination"
            ],
            "dispute_resolution": [
                "governing law", "jurisdiction", "arbitration", "mediation", 
                "dispute resolution", "venue"
            ],
            "court_language": [
                "respectfully submitted", "comes now", "honorable court", 
                "prayer for relief", "wherefore premises considered"
            ],
            "legal_citations": [
                r"\d+\s+F\.\d+d?\s+\d+", r"\d+\s+U\.S\.C\.", r"Fed\.\s*R\.",
                r"\d+\s+S\.\s*Ct\.", r"\d+\s+L\.\s*Ed\."
            ]
        }
    
    def _build_document_signatures(self) -> None:
        """Build document type signatures for pattern matching"""
        self._document_signatures = {
            DocumentType.CONTRACT: {
                "this agreement", "parties agree", "in witness whereof", 
                "executed as of", "binding upon", "consideration received"
            },
            DocumentType.AFFIDAVIT: {
                "being duly sworn", "under penalty of perjury", "notary public",
                "subscribed and sworn", "acknowledged before me"
            },
            DocumentType.MOTION: {
                "respectfully moves", "motion for summary judgment", "motion to dismiss",
                "comes now", "prayer for relief", "wherefore"
            },
            DocumentType.COMPLAINT: {
                "cause of action", "plaintiff alleges", "jurisdiction and venue",
                "jury trial demanded", "damages in excess of"
            },
            DocumentType.LETTER: {
                "dear sir or madam", "to whom it may concern", "yours truly",
                "best regards", "sincerely yours"
            }
        }
    
    async def analyze(self, document_text: str, metadata: Optional[Dict[str, Any]] = None) -> AnalysisResult:
        """
        Classify the legal document
        
        Args:
            document_text: The legal document text to classify
            metadata: Optional document metadata
            
        Returns:
            AnalysisResult containing classification results
        """
        start_time = datetime.utcnow()
        
        try:
            # Validate input
            self.validate_input(document_text)
            
            # Create base result
            result = self._create_base_result(metadata.get("document_id", "") if metadata else "")
            
            # Process document with spaCy
            doc = self.nlp(document_text)
            result.tokens_analyzed = len(doc)
            
            # Perform classification
            classification = await self._classify_document(document_text, doc)
            result.classification = classification
            
            # Calculate overall confidence
            result.confidence_score = classification.confidence
            
            # Add classification metadata
            result.metadata.update({
                "classification_method": "rule_based_ml",
                "features_analyzed": ["keywords", "phrases", "patterns", "structure"],
                "document_length": len(document_text),
                "sentence_count": len(list(doc.sents))
            })
            
            # Set completion status
            result.completed_at = datetime.utcnow()
            result.processing_time = (result.completed_at - start_time).total_seconds()
            result.status = "completed"
            
            return result
            
        except Exception as e:
            result = self._create_base_result(metadata.get("document_id", "") if metadata else "")
            result.status = "failed"
            result.error_message = str(e)
            result.completed_at = datetime.utcnow()
            result.processing_time = (result.completed_at - start_time).total_seconds()
            
            if isinstance(e, (ClassificationError, ModelError)):
                raise
            else:
                raise ClassificationError(f"Document classification failed: {str(e)}")
    
    async def _classify_document(self, document_text: str, doc) -> Classification:
        """Perform the actual document classification"""
        
        # Normalize text for pattern matching
        text_lower = document_text.lower()
        
        # Score each document type
        type_scores = {}
        
        for doc_type, rules in self._classification_rules.items():
            score = 0.0
            matches = []
            
            # Keyword matching
            keyword_score = self._score_keywords(text_lower, rules["keywords"])
            score += keyword_score * 0.3
            
            # Phrase matching
            phrase_score = self._score_phrases(text_lower, rules["phrases"])
            score += phrase_score * 0.3
            
            # Pattern matching
            pattern_score = self._score_patterns(document_text, rules["patterns"])
            score += pattern_score * 0.2
            
            # Signature matching
            signature_score = self._score_signatures(text_lower, doc_type)
            score += signature_score * 0.2
            
            type_scores[doc_type] = min(1.0, score)
        
        # Find best match
        best_type = max(type_scores, key=type_scores.get)
        best_score = type_scores[best_type]
        
        # Determine sub-categories
        sub_categories = await self._identify_subcategories(document_text, best_type)
        
        # Create classification result
        classification = Classification(
            document_type=best_type if best_score >= self._classification_rules[best_type]["confidence_threshold"] else DocumentType.UNKNOWN,
            confidence=best_score,
            sub_categories=sub_categories,
            metadata={
                "all_scores": {doc_type.value: score for doc_type, score in type_scores.items()},
                "classification_features": self._extract_classification_features(document_text, doc)
            }
        )
        
        return classification
    
    def _score_keywords(self, text_lower: str, keywords: List[str]) -> float:
        """Score based on keyword presence"""
        found_keywords = sum(1 for keyword in keywords if keyword.lower() in text_lower)
        return found_keywords / len(keywords) if keywords else 0.0
    
    def _score_phrases(self, text_lower: str, phrases: List[str]) -> float:
        """Score based on phrase presence"""
        found_phrases = sum(1 for phrase in phrases if phrase.lower() in text_lower)
        return found_phrases / len(phrases) if phrases else 0.0
    
    def _score_patterns(self, document_text: str, patterns: List[str]) -> float:
        """Score based on regex pattern matches"""
        total_matches = 0
        for pattern in patterns:
            matches = re.findall(pattern, document_text, re.IGNORECASE)
            total_matches += len(matches)
        
        # Normalize by document length and pattern count
        normalized_score = min(1.0, total_matches / (len(patterns) * 2))
        return normalized_score
    
    def _score_signatures(self, text_lower: str, doc_type: DocumentType) -> float:
        """Score based on document type signatures"""
        if doc_type not in self._document_signatures:
            return 0.0
        
        signatures = self._document_signatures[doc_type]
        found_signatures = sum(1 for sig in signatures if sig.lower() in text_lower)
        return found_signatures / len(signatures) if signatures else 0.0
    
    async def _identify_subcategories(self, document_text: str, doc_type: DocumentType) -> List[str]:
        """Identify document subcategories"""
        subcategories = []
        text_lower = document_text.lower()
        
        # Contract subcategories
        if doc_type == DocumentType.CONTRACT:
            contract_types = {
                "employment": ["employment", "employee", "employer", "job", "salary", "benefits"],
                "service": ["services", "provider", "client", "deliverables", "scope of work"],
                "sales": ["purchase", "sale", "buyer", "seller", "goods", "products"],
                "licensing": ["license", "intellectual property", "royalty", "trademark", "copyright"],
                "nda": ["confidential", "non-disclosure", "proprietary", "trade secret"]
            }
            
            for subtype, keywords in contract_types.items():
                if any(keyword in text_lower for keyword in keywords):
                    subcategories.append(subtype)
        
        # Letter subcategories
        elif doc_type == DocumentType.LETTER:
            letter_types = {
                "demand": ["demand", "payment", "overdue", "collection", "owe"],
                "cease_desist": ["cease", "desist", "infringe", "violation", "unauthorized"],
                "notice": ["notice", "notify", "inform", "advise", "aware"],
                "opinion": ["opinion", "analysis", "recommend", "advise", "counsel"]
            }
            
            for subtype, keywords in letter_types.items():
                if any(keyword in text_lower for keyword in keywords):
                    subcategories.append(subtype)
        
        # Motion subcategories
        elif doc_type == DocumentType.MOTION:
            motion_types = {
                "summary_judgment": ["summary judgment", "no genuine issue"],
                "dismiss": ["motion to dismiss", "12(b)(6)", "failure to state"],
                "compel": ["motion to compel", "discovery", "interrogatories"],
                "preliminary_injunction": ["preliminary injunction", "irreparable harm", "balance of hardships"]
            }
            
            for subtype, keywords in motion_types.items():
                if any(keyword in text_lower for keyword in keywords):
                    subcategories.append(subtype)
        
        return subcategories
    
    def _extract_classification_features(self, document_text: str, doc) -> Dict[str, Any]:
        """Extract features used for classification"""
        
        # Document structure analysis
        lines = document_text.split('\n')
        paragraphs = [p.strip() for p in document_text.split('\n\n') if p.strip()]
        
        # Legal language density
        legal_words = ["whereas", "therefore", "hereby", "therein", "hereafter", "notwithstanding"]
        legal_word_count = sum(1 for word in doc if word.text.lower() in legal_words)
        legal_density = legal_word_count / len(doc) if len(doc) > 0 else 0
        
        # Date pattern analysis
        date_patterns = [
            r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
            r'\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b'
        ]
        date_count = sum(len(re.findall(pattern, document_text)) for pattern in date_patterns)
        
        # Citation analysis
        citation_patterns = [
            r'\d+\s+F\.\d+d?\s+\d+',  # Federal reporters
            r'\d+\s+U\.S\.C\.\s*§?\s*\d+',  # US Code
            r'Fed\.\s*R\.'  # Federal Rules
        ]
        citation_count = sum(len(re.findall(pattern, document_text)) for pattern in citation_patterns)
        
        return {
            "line_count": len(lines),
            "paragraph_count": len(paragraphs),
            "sentence_count": len(list(doc.sents)),
            "legal_language_density": legal_density,
            "date_mentions": date_count,
            "legal_citations": citation_count,
            "average_sentence_length": sum(len(sent) for sent in doc.sents) / len(list(doc.sents)) if list(doc.sents) else 0,
            "has_signature_block": bool(re.search(r'signature|signed|executed', document_text, re.IGNORECASE)),
            "has_date_line": bool(re.search(r'date[d:]', document_text, re.IGNORECASE)),
            "formal_language_indicators": len(re.findall(r'\b(respectfully|hereby|whereas|therefore)\b', document_text, re.IGNORECASE))
        }
    
    def get_version(self) -> str:
        """Get the version of this analyzer"""
        return self.VERSION