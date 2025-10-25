"""
RemedyCompiler - Legal Remedy Suggestion Engine
==============================================

This module provides intelligent legal remedy suggestions based on document
analysis, legal precedents, and best practices. It recommends specific actions,
contract modifications, and legal strategies to address identified issues.

Features:
- Issue-specific remedy generation
- Legal precedent matching
- Risk mitigation strategies  
- Contract clause suggestions
- Compliance recommendations
- Priority-based remedy ranking
"""

import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass
import re

from .base import BaseAnalyzer, AnalysisResult, Remedy, LegalIssue, LegalIssueType, SeverityLevel
from .exceptions import AnalysisError, ModelError


@dataclass
class RemedyTemplate:
    """Template for generating remedies"""
    id: str
    title: str
    description: str
    category: str
    applicable_issues: List[LegalIssueType]
    priority: SeverityLevel
    implementation_steps: List[str]
    legal_basis: List[str]
    template_variables: Dict[str, str]


@dataclass
class LegalPrecedent:
    """Legal precedent or case law reference"""
    case_name: str
    citation: str
    jurisdiction: str
    summary: str
    applicable_issues: List[LegalIssueType]
    remedy_guidance: str


class RemedyCompiler(BaseAnalyzer):
    """
    AI-powered legal remedy compiler
    
    Generates remedies for:
    - Contract contradictions and ambiguities
    - Compliance issues and violations
    - Risk mitigation strategies
    - Document structure improvements
    - Legal precedent alignment
    - Best practice recommendations
    """
    
    VERSION = "1.0.0"
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._remedy_templates: Dict[str, RemedyTemplate] = {}
        self._legal_precedents: List[LegalPrecedent] = []
        self._remedy_categories: Dict[str, List[str]] = {}
        self._risk_mitigation_strategies: Dict[LegalIssueType, List[str]] = {}
    
    def _initialize(self) -> None:
        """Initialize the remedy compiler"""
        self._load_remedy_templates()
        self._load_legal_precedents()
        self._initialize_remedy_categories()
        self._load_risk_mitigation_strategies()
    
    def _load_remedy_templates(self) -> None:
        """Load predefined remedy templates"""
        
        templates = [
            RemedyTemplate(
                id="contradiction_clarification",
                title="Clarify Contradictory Terms",
                description="Add clarifying language to resolve contradictory statements",
                category="Contract Clarification",
                applicable_issues=[LegalIssueType.CONTRADICTION, LegalIssueType.AMBIGUITY],
                priority=SeverityLevel.HIGH,
                implementation_steps=[
                    "Identify the specific contradictory provisions",
                    "Determine the intended meaning through party consultation",
                    "Draft clarifying language that resolves the contradiction",
                    "Add definitions section if terms need clarification",
                    "Include hierarchy clause to resolve future conflicts"
                ],
                legal_basis=[
                    "Contract interpretation doctrine of contra proferentem",
                    "Parol evidence rule considerations",
                    "Good faith and fair dealing principles"
                ],
                template_variables={
                    "conflicting_sections": "Sections {section1} and {section2}",
                    "clarification_text": "For the avoidance of doubt, {clarifying_statement}"
                }
            ),
            
            RemedyTemplate(
                id="missing_clause_addition",
                title="Add Essential Missing Clauses",
                description="Include critical clauses that are typically required",
                category="Contract Completeness",
                applicable_issues=[LegalIssueType.MISSING_CLAUSE, LegalIssueType.COMPLIANCE_ISSUE],
                priority=SeverityLevel.HIGH,
                implementation_steps=[
                    "Review industry-standard contract provisions",
                    "Identify jurisdiction-specific requirements",
                    "Draft appropriate clauses using standard language",
                    "Ensure clauses integrate properly with existing terms",
                    "Update cross-references and defined terms"
                ],
                legal_basis=[
                    "Industry best practices",
                    "Jurisdictional requirements",
                    "Risk management principles"
                ],
                template_variables={
                    "clause_type": "{clause_name}",
                    "standard_language": "{template_text}"
                }
            ),
            
            RemedyTemplate(
                id="compliance_update",
                title="Update for Regulatory Compliance",
                description="Modify contract to meet current regulatory requirements",
                category="Compliance",
                applicable_issues=[LegalIssueType.COMPLIANCE_ISSUE],
                priority=SeverityLevel.CRITICAL,
                implementation_steps=[
                    "Research current regulatory requirements",
                    "Identify non-compliant provisions",
                    "Draft compliant alternative language",
                    "Add compliance certification clauses",
                    "Include regulatory change adaptation mechanisms"
                ],
                legal_basis=[
                    "Applicable federal regulations",
                    "State-specific compliance requirements",
                    "Industry regulatory standards"
                ],
                template_variables={
                    "regulation": "{regulatory_citation}",
                    "compliance_text": "{compliant_language}"
                }
            ),
            
            RemedyTemplate(
                id="risk_mitigation",
                title="Add Risk Mitigation Provisions",
                description="Include clauses to mitigate identified legal risks",
                category="Risk Management",
                applicable_issues=[LegalIssueType.RISK_FACTOR],
                priority=SeverityLevel.HIGH,
                implementation_steps=[
                    "Assess specific risk factors identified",
                    "Research appropriate risk mitigation clauses",
                    "Draft risk-specific protective language",
                    "Include limitation of liability provisions if appropriate",
                    "Add insurance and indemnification requirements"
                ],
                legal_basis=[
                    "Risk management best practices",
                    "Liability limitation precedents",
                    "Insurance industry standards"
                ],
                template_variables={
                    "risk_type": "{identified_risk}",
                    "mitigation_clause": "{protective_language}"
                }
            ),
            
            RemedyTemplate(
                id="reference_correction",
                title="Correct Cross-References",
                description="Fix broken or incorrect internal references",
                category="Document Structure",
                applicable_issues=[LegalIssueType.REFERENCE_ERROR],
                priority=SeverityLevel.MEDIUM,
                implementation_steps=[
                    "Audit all cross-references in document",
                    "Verify target sections exist and are correctly numbered",
                    "Update incorrect section references",
                    "Add section titles for clarity",
                    "Consider adding table of contents for complex documents"
                ],
                legal_basis=[
                    "Document clarity and enforceability principles",
                    "Contract interpretation standards"
                ],
                template_variables={
                    "broken_reference": "Section {old_reference}",
                    "correct_reference": "Section {new_reference}"
                }
            ),
            
            RemedyTemplate(
                id="format_standardization",
                title="Standardize Document Format",
                description="Improve document structure and formatting consistency",
                category="Document Quality",
                applicable_issues=[LegalIssueType.FORMATTING_ERROR],
                priority=SeverityLevel.LOW,
                implementation_steps=[
                    "Review document formatting standards",
                    "Standardize section numbering and headers",
                    "Ensure consistent use of defined terms",
                    "Standardize date and monetary formats",
                    "Add signature blocks and execution formalities"
                ],
                legal_basis=[
                    "Professional document standards",
                    "Legal document best practices"
                ],
                template_variables={
                    "format_issue": "{formatting_problem}",
                    "standard_format": "{correct_format}"
                }
            )
        ]
        
        self._remedy_templates = {template.id: template for template in templates}
    
    def _load_legal_precedents(self) -> None:
        """Load legal precedents for remedy guidance"""
        
        precedents = [
            LegalPrecedent(
                case_name="Frigaliment Importing Co. v. B.N.S. International Sales",
                citation="190 F. Supp. 116 (S.D.N.Y. 1960)",
                jurisdiction="Federal",
                summary="Court addressed ambiguous contract terms and the importance of clear definitions",
                applicable_issues=[LegalIssueType.AMBIGUITY, LegalIssueType.CONTRADICTION],
                remedy_guidance="Include detailed definitions section and clarify ambiguous terms through party intent analysis"
            ),
            
            LegalPrecedent(
                case_name="Hadley v. Baxendale",
                citation="9 Exch. 341 (1854)",
                jurisdiction="English Common Law",
                summary="Established foreseeability standard for consequential damages",
                applicable_issues=[LegalIssueType.RISK_FACTOR],
                remedy_guidance="Include specific limitation of liability clauses and consequential damages exclusions"
            ),
            
            LegalPrecedent(
                case_name="Lucy v. Zehmer",
                citation="196 Va. 493, 84 S.E.2d 516 (1954)",
                jurisdiction="Virginia",
                summary="Objective test for contract formation and mutual assent",
                applicable_issues=[LegalIssueType.AMBIGUITY, LegalIssueType.MISSING_CLAUSE],
                remedy_guidance="Ensure clear expressions of mutual assent and consideration"
            )
        ]
        
        self._legal_precedents = precedents
    
    def _initialize_remedy_categories(self) -> None:
        """Initialize remedy categorization system"""
        
        self._remedy_categories = {
            "Contract Clarification": [
                "Term definitions", "Ambiguity resolution", "Contradiction elimination",
                "Intent clarification", "Language simplification"
            ],
            
            "Compliance": [
                "Regulatory updates", "Statutory requirements", "Industry standards",
                "Licensing compliance", "Data protection"
            ],
            
            "Risk Management": [
                "Liability limitation", "Insurance requirements", "Indemnification",
                "Force majeure", "Dispute resolution"
            ],
            
            "Document Structure": [
                "Section organization", "Cross-references", "Formatting",
                "Signature blocks", "Execution formalities"
            ],
            
            "Performance Obligations": [
                "Delivery terms", "Payment schedules", "Performance standards",
                "Acceptance criteria", "Milestone definitions"
            ],
            
            "Termination & Breach": [
                "Termination triggers", "Cure periods", "Breach remedies",
                "Survival clauses", "Return obligations"
            ]
        }
    
    def _load_risk_mitigation_strategies(self) -> None:
        """Load risk mitigation strategies by issue type"""
        
        self._risk_mitigation_strategies = {
            LegalIssueType.CONTRADICTION: [
                "Add hierarchy clause to resolve conflicts between provisions",
                "Include integration clause stating contract contains entire agreement",
                "Use clear, unambiguous language throughout",
                "Add definitions section for key terms"
            ],
            
            LegalIssueType.AMBIGUITY: [
                "Define ambiguous terms in definitions section",
                "Use specific rather than general language",
                "Include examples or illustrations where helpful",
                "Add interpretation guidelines clause"
            ],
            
            LegalIssueType.MISSING_CLAUSE: [
                "Add standard industry-required clauses",
                "Include jurisdiction and governing law provisions",
                "Add dispute resolution mechanisms",
                "Include force majeure and assignment clauses"
            ],
            
            LegalIssueType.COMPLIANCE_ISSUE: [
                "Research and incorporate current regulatory requirements",
                "Add compliance certification requirements",
                "Include regulatory change adaptation mechanisms",
                "Add audit and inspection rights"
            ],
            
            LegalIssueType.RISK_FACTOR: [
                "Add appropriate limitation of liability clauses",
                "Include comprehensive indemnification provisions",
                "Require adequate insurance coverage",
                "Add termination rights for material breaches"
            ]
        }
    
    async def analyze(self, document_text: str, metadata: Optional[Dict[str, Any]] = None) -> AnalysisResult:
        """
        Analyze issues and generate remedies
        
        Args:
            document_text: The legal document text
            metadata: Optional metadata including detected issues
            
        Returns:
            AnalysisResult containing generated remedies
        """
        start_time = datetime.utcnow()
        
        try:
            # Validate input
            self.validate_input(document_text)
            
            # Create base result
            result = self._create_base_result(metadata.get("document_id", "") if metadata else "")
            
            # Get issues from metadata or analyze document
            issues = []
            if metadata and "detected_issues" in metadata:
                issues = metadata["detected_issues"]
            else:
                # If no issues provided, perform basic issue detection
                issues = await self._detect_basic_issues(document_text)
            
            # Generate remedies for each issue
            all_remedies = []
            for issue in issues:
                remedies = await self._generate_remedies_for_issue(issue, document_text)
                all_remedies.extend(remedies)
            
            # Add general best practice remedies
            general_remedies = await self._generate_general_remedies(document_text)
            all_remedies.extend(general_remedies)
            
            # Remove duplicates and prioritize
            unique_remedies = self._deduplicate_and_prioritize(all_remedies)
            
            # Add remedies to result
            for remedy in unique_remedies:
                result.add_remedy(remedy)
            
            # Calculate confidence score
            result.confidence_score = self._calculate_remedy_confidence(unique_remedies, issues)
            
            # Add metadata
            result.metadata.update({
                "remedy_generation_method": "template_based_ai",
                "total_issues_addressed": len(issues),
                "remedy_categories": list(set(remedy.category for remedy in unique_remedies)),
                "precedents_referenced": len(self._legal_precedents)
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
            
            if isinstance(e, (AnalysisError, ModelError)):
                raise
            else:
                raise AnalysisError(f"Remedy compilation failed: {str(e)}", "RemedyCompiler")
    
    async def _detect_basic_issues(self, document_text: str) -> List[LegalIssue]:
        """Perform basic issue detection if no issues provided"""
        issues = []
        
        # Check for common missing clauses
        essential_clauses = [
            ("governing law", "governing law|applicable law|laws of", LegalIssueType.MISSING_CLAUSE),
            ("dispute resolution", "arbitration|mediation|dispute", LegalIssueType.MISSING_CLAUSE),
            ("termination", "terminate|termination|end this agreement", LegalIssueType.MISSING_CLAUSE),
            ("force majeure", "force majeure|act of god|beyond.*control", LegalIssueType.MISSING_CLAUSE)
        ]
        
        for clause_name, pattern, issue_type in essential_clauses:
            if not re.search(pattern, document_text, re.IGNORECASE):
                issues.append(LegalIssue(
                    type=issue_type,
                    severity=SeverityLevel.MEDIUM,
                    title=f"Missing {clause_name.title()} Clause",
                    description=f"Document appears to lack a {clause_name} provision",
                    confidence=0.8
                ))
        
        return issues
    
    async def _generate_remedies_for_issue(self, issue: LegalIssue, document_text: str) -> List[Remedy]:
        """Generate specific remedies for a detected issue"""
        remedies = []
        
        # Find applicable remedy templates
        applicable_templates = [
            template for template in self._remedy_templates.values()
            if issue.type in template.applicable_issues
        ]
        
        # Generate remedies from templates
        for template in applicable_templates:
            remedy = await self._create_remedy_from_template(template, issue, document_text)
            if remedy:
                remedies.append(remedy)
        
        # Add issue-specific remedies
        specific_remedies = await self._generate_issue_specific_remedies(issue, document_text)
        remedies.extend(specific_remedies)
        
        return remedies
    
    async def _create_remedy_from_template(self, template: RemedyTemplate, issue: LegalIssue, document_text: str) -> Optional[Remedy]:
        """Create a remedy from a template"""
        
        # Customize template for specific issue
        customized_steps = []
        for step in template.implementation_steps:
            # Simple template variable substitution
            customized_step = step
            if "{issue_description}" in step:
                customized_step = step.replace("{issue_description}", issue.description)
            customized_steps.append(customized_step)
        
        # Find relevant legal precedents
        relevant_precedents = [
            prec for prec in self._legal_precedents
            if issue.type in prec.applicable_issues
        ]
        
        legal_basis = template.legal_basis.copy()
        for precedent in relevant_precedents[:2]:  # Limit to 2 precedents
            legal_basis.append(f"{precedent.case_name}: {precedent.remedy_guidance}")
        
        return Remedy(
            title=template.title,
            description=f"{template.description}: {issue.description}",
            category=template.category,
            priority=template.priority,
            applicable_issues=[issue.id],
            implementation_steps=customized_steps,
            legal_basis=legal_basis,
            estimated_impact=self._estimate_remedy_impact(template, issue),
            metadata={
                "template_id": template.id,
                "issue_severity": issue.severity.value,
                "precedents_count": len(relevant_precedents)
            }
        )
    
    async def _generate_issue_specific_remedies(self, issue: LegalIssue, document_text: str) -> List[Remedy]:
        """Generate remedies specific to the issue context"""
        remedies = []
        
        # Get risk mitigation strategies
        if issue.type in self._risk_mitigation_strategies:
            strategies = self._risk_mitigation_strategies[issue.type]
            
            remedy = Remedy(
                title=f"Mitigate {issue.title}",
                description=f"Implement specific strategies to address: {issue.description}",
                category="Risk Mitigation",
                priority=issue.severity,
                applicable_issues=[issue.id],
                implementation_steps=strategies,
                legal_basis=["Risk management best practices", "Legal precedent analysis"],
                estimated_impact="Reduces legal risk and improves contract enforceability"
            )
            remedies.append(remedy)
        
        return remedies
    
    async def _generate_general_remedies(self, document_text: str) -> List[Remedy]:
        """Generate general best practice remedies"""
        remedies = []
        
        # Document structure improvements
        if len(document_text.split('\n')) < 10:  # Simple heuristic for short documents
            remedies.append(Remedy(
                title="Improve Document Structure",
                description="Add proper sectioning and organization to improve readability",
                category="Document Quality",
                priority=SeverityLevel.LOW,
                implementation_steps=[
                    "Add clear section headers",
                    "Use numbered or lettered subsections",
                    "Include table of contents for longer documents",
                    "Standardize formatting throughout"
                ],
                legal_basis=["Document clarity best practices"],
                estimated_impact="Improves document interpretation and reduces disputes"
            ))
        
        # General legal review recommendation
        remedies.append(Remedy(
            title="Professional Legal Review",
            description="Have document reviewed by qualified legal counsel",
            category="Legal Validation",
            priority=SeverityLevel.MEDIUM,
            implementation_steps=[
                "Engage qualified attorney in relevant jurisdiction",
                "Review for compliance with current law",
                "Ensure terms align with business objectives",
                "Validate enforceability of key provisions"
            ],
            legal_basis=["Professional legal standards", "Due diligence requirements"],
            estimated_impact="Ensures legal compliance and enforceability"
        ))
        
        return remedies
    
    def _deduplicate_and_prioritize(self, remedies: List[Remedy]) -> List[Remedy]:
        """Remove duplicate remedies and sort by priority"""
        
        # Simple deduplication by title
        seen_titles = set()
        unique_remedies = []
        
        for remedy in remedies:
            if remedy.title not in seen_titles:
                unique_remedies.append(remedy)
                seen_titles.add(remedy.title)
        
        # Sort by priority (Critical -> High -> Medium -> Low -> Info)
        priority_order = {
            SeverityLevel.CRITICAL: 0,
            SeverityLevel.HIGH: 1,
            SeverityLevel.MEDIUM: 2,
            SeverityLevel.LOW: 3,
            SeverityLevel.INFO: 4
        }
        
        return sorted(unique_remedies, key=lambda r: priority_order.get(r.priority, 5))
    
    def _estimate_remedy_impact(self, template: RemedyTemplate, issue: LegalIssue) -> str:
        """Estimate the impact of implementing a remedy"""
        
        impact_map = {
            SeverityLevel.CRITICAL: "Significantly reduces legal risk and ensures compliance",
            SeverityLevel.HIGH: "Substantially improves contract enforceability and reduces disputes",
            SeverityLevel.MEDIUM: "Moderately enhances document clarity and legal protection",
            SeverityLevel.LOW: "Provides minor improvements to document quality",
            SeverityLevel.INFO: "Offers best practice enhancement"
        }
        
        return impact_map.get(template.priority, "Improves overall document quality")
    
    def _calculate_remedy_confidence(self, remedies: List[Remedy], issues: List[LegalIssue]) -> float:
        """Calculate confidence score for remedy recommendations"""
        
        if not remedies:
            return 0.5
        
        # Base confidence on template matching and issue coverage
        template_based_count = sum(1 for remedy in remedies if "template_id" in remedy.metadata)
        template_confidence = template_based_count / len(remedies) if remedies else 0
        
        # Confidence increases with more comprehensive issue coverage
        issue_coverage = len(issues) / max(1, len(remedies)) if issues else 1
        coverage_confidence = min(1.0, issue_coverage)
        
        # Weight factors
        final_confidence = (template_confidence * 0.6) + (coverage_confidence * 0.4)
        
        return min(0.95, max(0.6, final_confidence))
    
    def get_version(self) -> str:
        """Get the version of this analyzer"""
        return self.VERSION