"""
ContradictionDetector - AI-Powered Legal Contradiction Detection
==============================================================

This module provides advanced contradiction detection capabilities for legal documents.
It identifies logical inconsistencies, conflicting terms, and potential legal issues
using natural language processing and legal rule validation.

Features:
- Term conflict detection
- Date/timeline contradiction analysis  
- Obligation inconsistency identification
- Cross-reference validation
- Legal precedent checking
"""

import asyncio
import re
from datetime import datetime
from typing import Dict, List, Optional, Any, Set, Tuple
import spacy
from dataclasses import dataclass

from .base import BaseAnalyzer, AnalysisResult, LegalIssue, LegalIssueType, SeverityLevel
from .exceptions import DetectionError, ModelError, ValidationError


@dataclass 
class ContradictionRule:
    """Represents a contradiction detection rule"""
    id: str
    name: str
    pattern: str
    severity: SeverityLevel
    description: str
    categories: List[str]


class ContradictionDetector(BaseAnalyzer):
    """
    AI-powered contradiction detector for legal documents
    
    Identifies various types of contradictions including:
    - Conflicting terms and definitions
    - Date/timeline inconsistencies
    - Obligation conflicts
    - Cross-reference errors
    - Legal precedent violations
    """
    
    VERSION = "1.0.0"
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.nlp = None
        self.contradiction_rules: List[ContradictionRule] = []
        self._legal_terms: Set[str] = set()
        self._date_patterns: List[re.Pattern] = []
    
    def _initialize(self) -> None:
        """Initialize the contradiction detector"""
        try:
            # Load spaCy model
            model_name = self.config.get("nlp_model", "en_core_web_sm")
            self.nlp = spacy.load(model_name)
        except OSError:
            raise ModelError(f"Failed to load spaCy model: {model_name}")
        
        # Initialize contradiction rules
        self._load_contradiction_rules()
        
        # Initialize legal terms dictionary
        self._load_legal_terms()
        
        # Initialize date patterns
        self._initialize_date_patterns()
    
    def _load_contradiction_rules(self) -> None:
        """Load predefined contradiction detection rules"""
        self.contradiction_rules = [
            ContradictionRule(
                id="term_conflict",
                name="Conflicting Term Definitions",
                pattern=r"(?i)\b(shall|will|must)\s+(not\s+)?\w+.*\b(shall|will|must)\s+(not\s+)?\w+",
                severity=SeverityLevel.HIGH,
                description="Conflicting obligation or requirement statements",
                categories=["obligations", "definitions"]
            ),
            ContradictionRule(
                id="date_conflict",
                name="Date Inconsistencies", 
                pattern=r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",
                severity=SeverityLevel.MEDIUM,
                description="Potentially conflicting dates in document",
                categories=["dates", "timelines"]
            ),
            ContradictionRule(
                id="amount_conflict",
                name="Monetary Amount Conflicts",
                pattern=r"\$[\d,]+\.?\d*",
                severity=SeverityLevel.HIGH,
                description="Conflicting monetary amounts or calculations", 
                categories=["financial", "calculations"]
            ),
            ContradictionRule(
                id="party_reference",
                name="Inconsistent Party References",
                pattern=r"\b(party|parties|entity|entities)\b",
                severity=SeverityLevel.MEDIUM,
                description="Inconsistent references to contract parties",
                categories=["parties", "references"]
            ),
            ContradictionRule(
                id="jurisdiction_conflict",
                name="Conflicting Jurisdiction Clauses",
                pattern=r"\b(governed?\s+by|jurisdiction|court|venue)\b",
                severity=SeverityLevel.HIGH,
                description="Multiple or conflicting jurisdiction clauses",
                categories=["jurisdiction", "legal"]
            )
        ]
    
    def _load_legal_terms(self) -> None:
        """Load legal terminology dictionary"""
        self._legal_terms = {
            # Contract terms
            "whereas", "therefore", "notwithstanding", "heretofore", "herein",
            "hereof", "hereby", "hereafter", "thereunder", "thereof", "therein",
            
            # Obligation terms
            "shall", "will", "must", "may", "should", "ought", "covenant",
            "agree", "undertake", "guarantee", "warrant", "represent",
            
            # Legal concepts
            "consideration", "breach", "default", "remedy", "damages", "liability",
            "indemnification", "force majeure", "act of god", "material adverse",
            
            # Time-related terms
            "effective date", "commencement", "expiration", "termination", "renewal",
            "notice period", "cure period", "grace period", "statute of limitations"
        }
    
    def _initialize_date_patterns(self) -> None:
        """Initialize regex patterns for date detection"""
        self._date_patterns = [
            re.compile(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b'),  # MM/DD/YYYY or MM-DD-YYYY
            re.compile(r'\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b'),    # YYYY/MM/DD or YYYY-MM-DD
            re.compile(r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b', re.IGNORECASE),
            re.compile(r'\b\d{1,2}\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b', re.IGNORECASE)
        ]
    
    async def analyze(self, document_text: str, metadata: Optional[Dict[str, Any]] = None) -> AnalysisResult:
        """
        Analyze document for contradictions and inconsistencies
        
        Args:
            document_text: The legal document text to analyze
            metadata: Optional document metadata
            
        Returns:
            AnalysisResult containing detected contradictions and issues
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
            
            # Run contradiction detection analyses
            contradictions = []
            
            # 1. Term definition conflicts
            term_conflicts = await self._detect_term_conflicts(doc, document_text)
            contradictions.extend(term_conflicts)
            
            # 2. Date inconsistencies
            date_conflicts = await self._detect_date_conflicts(document_text)
            contradictions.extend(date_conflicts)
            
            # 3. Monetary amount conflicts
            amount_conflicts = await self._detect_amount_conflicts(document_text)
            contradictions.extend(amount_conflicts)
            
            # 4. Cross-reference validation
            reference_errors = await self._detect_reference_errors(doc, document_text)
            contradictions.extend(reference_errors)
            
            # 5. Legal precedent checking
            precedent_issues = await self._check_legal_precedents(doc)
            contradictions.extend(precedent_issues)
            
            # Add all detected issues to result
            for contradiction in contradictions:
                result.add_issue(contradiction)
            
            # Calculate confidence score
            result.confidence_score = self._calculate_confidence_score(contradictions, len(doc))
            
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
            
            if isinstance(e, (DetectionError, ModelError, ValidationError)):
                raise
            else:
                raise DetectionError(f"Contradiction detection failed: {str(e)}", "general")
    
    async def _detect_term_conflicts(self, doc, document_text: str) -> List[LegalIssue]:
        """Detect conflicting term definitions and obligations"""
        conflicts = []
        
        # Find obligation statements
        obligation_patterns = [
            (r'\b(\w+)\s+shall\s+(not\s+)?(\w+)', "obligation"),
            (r'\b(\w+)\s+must\s+(not\s+)?(\w+)', "requirement"), 
            (r'\b(\w+)\s+will\s+(not\s+)?(\w+)', "commitment")
        ]
        
        obligations = {}
        
        for pattern, category in obligation_patterns:
            matches = re.finditer(pattern, document_text, re.IGNORECASE)
            for match in matches:
                entity = match.group(1).lower()
                negation = match.group(2) is not None
                action = match.group(3).lower()
                
                key = f"{entity}_{action}"
                if key in obligations:
                    # Check for contradiction
                    if obligations[key]["negation"] != negation:
                        conflicts.append(LegalIssue(
                            type=LegalIssueType.CONTRADICTION,
                            severity=SeverityLevel.HIGH,
                            title=f"Conflicting {category} for {entity}",
                            description=f"Document contains conflicting statements about {entity}'s obligation to {action}",
                            location={"start": match.start(), "end": match.end()},
                            confidence=0.9,
                            suggestions=[
                                f"Review and clarify the obligation of {entity} regarding {action}",
                                "Ensure consistency in obligation statements throughout document"
                            ]
                        ))
                else:
                    obligations[key] = {"negation": negation, "location": match.span()}
        
        return conflicts
    
    async def _detect_date_conflicts(self, document_text: str) -> List[LegalIssue]:
        """Detect date inconsistencies and timeline conflicts"""
        conflicts = []
        dates_found = []
        
        # Extract all dates
        for pattern in self._date_patterns:
            matches = pattern.finditer(document_text)
            for match in matches:
                dates_found.append({
                    "text": match.group(),
                    "location": match.span(),
                    "context": document_text[max(0, match.start()-50):match.end()+50]
                })
        
        # Check for timeline inconsistencies
        if len(dates_found) > 1:
            # Simple heuristic: flag if same context mentions different dates
            for i, date1 in enumerate(dates_found):
                for j, date2 in enumerate(dates_found[i+1:], i+1):
                    if abs(date1["location"][0] - date2["location"][0]) < 200:  # Within 200 characters
                        if date1["text"] != date2["text"]:
                            conflicts.append(LegalIssue(
                                type=LegalIssueType.INCONSISTENCY,
                                severity=SeverityLevel.MEDIUM,
                                title="Potential Date Inconsistency",
                                description=f"Found different dates '{date1['text']}' and '{date2['text']}' in close proximity",
                                location={"dates": [date1["location"], date2["location"]]},
                                confidence=0.7,
                                suggestions=[
                                    "Verify that all dates are correct and consistent",
                                    "Consider using defined terms for important dates"
                                ]
                            ))
        
        return conflicts
    
    async def _detect_amount_conflicts(self, document_text: str) -> List[LegalIssue]:
        """Detect conflicting monetary amounts"""
        conflicts = []
        amount_pattern = re.compile(r'\$[\d,]+(?:\.\d{2})?')
        amounts_found = []
        
        matches = amount_pattern.finditer(document_text)
        for match in matches:
            amounts_found.append({
                "text": match.group(),
                "value": float(match.group().replace('$', '').replace(',', '')),
                "location": match.span(),
                "context": document_text[max(0, match.start()-100):match.end()+100]
            })
        
        # Check for amount inconsistencies in similar contexts
        for i, amount1 in enumerate(amounts_found):
            for j, amount2 in enumerate(amounts_found[i+1:], i+1):
                # If amounts are in similar context but different values
                if (abs(amount1["location"][0] - amount2["location"][0]) < 300 and 
                    amount1["value"] != amount2["value"]):
                    
                    conflicts.append(LegalIssue(
                        type=LegalIssueType.INCONSISTENCY,
                        severity=SeverityLevel.HIGH,
                        title="Monetary Amount Inconsistency",
                        description=f"Found different amounts '{amount1['text']}' and '{amount2['text']}' in related context",
                        location={"amounts": [amount1["location"], amount2["location"]]},
                        confidence=0.8,
                        suggestions=[
                            "Verify all monetary amounts are correct",
                            "Ensure calculations are accurate",
                            "Consider using defined terms for key amounts"
                        ]
                    ))
        
        return conflicts
    
    async def _detect_reference_errors(self, doc, document_text: str) -> List[LegalIssue]:
        """Detect cross-reference and citation errors"""
        errors = []
        
        # Find section references
        section_refs = re.finditer(r'Section\s+(\d+(?:\.\d+)*)', document_text, re.IGNORECASE)
        referenced_sections = set()
        
        for match in section_refs:
            section_num = match.group(1)
            referenced_sections.add(section_num)
        
        # Find actual section headers  
        section_headers = re.finditer(r'^(\d+(?:\.\d+)*)\s+', document_text, re.MULTILINE)
        actual_sections = set()
        
        for match in section_headers:
            section_num = match.group(1)
            actual_sections.add(section_num)
        
        # Check for broken references
        broken_refs = referenced_sections - actual_sections
        for ref in broken_refs:
            errors.append(LegalIssue(
                type=LegalIssueType.REFERENCE_ERROR,
                severity=SeverityLevel.MEDIUM,
                title=f"Broken Section Reference: {ref}",
                description=f"Document references Section {ref} which does not exist",
                confidence=0.95,
                suggestions=[
                    f"Add Section {ref} or update the reference",
                    "Review all section references for accuracy"
                ]
            ))
        
        return errors
    
    async def _check_legal_precedents(self, doc) -> List[LegalIssue]:
        """Check for potential legal precedent violations or issues"""
        issues = []
        
        # This is a simplified implementation - in production would integrate with legal databases
        common_issues = [
            {
                "pattern": r'\bforever\b',
                "issue": "Perpetual terms may be unenforceable",
                "severity": SeverityLevel.HIGH
            },
            {
                "pattern": r'\bunlimited\s+liability\b',
                "issue": "Unlimited liability clauses may be problematic", 
                "severity": SeverityLevel.HIGH
            },
            {
                "pattern": r'\bpenalty\b',
                "issue": "Penalty clauses may be unenforceable vs. liquidated damages",
                "severity": SeverityLevel.MEDIUM
            }
        ]
        
        for check in common_issues:
            matches = re.finditer(check["pattern"], doc.text, re.IGNORECASE)
            for match in matches:
                issues.append(LegalIssue(
                    type=LegalIssueType.COMPLIANCE_ISSUE,
                    severity=check["severity"],
                    title="Potential Legal Issue",
                    description=check["issue"],
                    location={"start": match.start(), "end": match.end()},
                    confidence=0.8,
                    suggestions=[
                        "Consult with legal counsel regarding this clause",
                        "Consider alternative language that achieves the same objective"
                    ]
                ))
        
        return issues
    
    def _calculate_confidence_score(self, contradictions: List[LegalIssue], token_count: int) -> float:
        """Calculate overall confidence score for the analysis"""
        if not contradictions:
            return 0.95  # High confidence when no issues found
        
        # Weight by severity and individual confidence
        total_weight = 0
        weighted_confidence = 0
        
        severity_weights = {
            SeverityLevel.CRITICAL: 1.0,
            SeverityLevel.HIGH: 0.8, 
            SeverityLevel.MEDIUM: 0.6,
            SeverityLevel.LOW: 0.4,
            SeverityLevel.INFO: 0.2
        }
        
        for issue in contradictions:
            weight = severity_weights.get(issue.severity, 0.5)
            total_weight += weight
            weighted_confidence += issue.confidence * weight
        
        if total_weight > 0:
            avg_confidence = weighted_confidence / total_weight
        else:
            avg_confidence = 0.5
        
        # Adjust based on document complexity
        complexity_factor = min(1.0, token_count / 1000)  # Normalize to 1000 tokens
        
        return min(0.99, avg_confidence * (0.7 + 0.3 * complexity_factor))
    
    def get_version(self) -> str:
        """Get the version of this analyzer"""
        return self.VERSION