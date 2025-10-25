"""
DocumentAnalyzer - Unified Legal Document Intelligence Engine
==========================================================

This module provides a comprehensive document analysis engine that combines
all LocalAgentCore modules into a unified interface. It orchestrates the
analysis workflow and provides integrated results.

Features:
- Orchestrates all analysis modules
- Provides unified analysis interface
- Manages analysis workflow and dependencies
- Caches and optimizes performance
- Generates comprehensive analysis reports
"""

import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
import json
from dataclasses import asdict

from .base import BaseAnalyzer, AnalysisResult, LegalIssue, Remedy, Classification, DocumentType, SeverityLevel
from .contradiction_detector import ContradictionDetector
from .instrument_classifier import InstrumentClassifier
from .remedy_compiler import RemedyCompiler
from .exceptions import AnalysisError, ModelError, ConfigurationError


class DocumentAnalyzer(BaseAnalyzer):
    """
    Comprehensive legal document analysis engine
    
    Combines all LocalAgentCore capabilities:
    - Document classification (InstrumentClassifier)
    - Contradiction detection (ContradictionDetector) 
    - Remedy generation (RemedyCompiler)
    - Integrated analysis and reporting
    """
    
    VERSION = "1.0.0"
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        # Initialize component analyzers first
        self.classifier: Optional[InstrumentClassifier] = None
        self.contradiction_detector: Optional[ContradictionDetector] = None
        self.remedy_compiler: Optional[RemedyCompiler] = None
        
        # Set analysis configuration before calling super().__init__()
        if config is None:
            config = {}
        self.enable_classification = config.get("enable_classification", True)
        self.enable_contradiction_detection = config.get("enable_contradiction_detection", True)
        self.enable_remedy_generation = config.get("enable_remedy_generation", True)
        self.parallel_processing = config.get("parallel_processing", True)
        
        super().__init__(config)
        
        # Cache for results
        self._analysis_cache: Dict[str, AnalysisResult] = {}
        self.enable_caching = self.config.get("enable_caching", True)
        
    def _initialize(self) -> None:
        """Initialize the document analyzer and its components"""
        
        try:
            # Initialize component analyzers with shared config
            component_config = self.config.get("component_config", {})
            
            if self.enable_classification:
                classifier_config = {**self.config, **component_config.get("classifier", {})}
                self.classifier = InstrumentClassifier(classifier_config)
            
            if self.enable_contradiction_detection:
                detector_config = {**self.config, **component_config.get("contradiction_detector", {})}
                self.contradiction_detector = ContradictionDetector(detector_config)
            
            if self.enable_remedy_generation:
                compiler_config = {**self.config, **component_config.get("remedy_compiler", {})}
                self.remedy_compiler = RemedyCompiler(compiler_config)
                
        except Exception as e:
            raise ConfigurationError(f"Failed to initialize DocumentAnalyzer components: {str(e)}")
    
    async def analyze(self, document_text: str, metadata: Optional[Dict[str, Any]] = None) -> AnalysisResult:
        """
        Perform comprehensive document analysis
        
        Args:
            document_text: The legal document text to analyze
            metadata: Optional document metadata
            
        Returns:
            AnalysisResult containing comprehensive analysis results
        """
        start_time = datetime.utcnow()
        
        try:
            # Validate input
            self.validate_input(document_text)
            
            # Check cache if enabled
            cache_key = self._generate_cache_key(document_text, metadata)
            if self.enable_caching and cache_key in self._analysis_cache:
                cached_result = self._analysis_cache[cache_key]
                # Update metadata to indicate cached result
                cached_result.metadata["cached_result"] = True
                cached_result.metadata["cache_hit_time"] = datetime.utcnow().isoformat()
                return cached_result
            
            # Create base result
            result = self._create_base_result(metadata.get("document_id", "") if metadata else "")
            result.tokens_analyzed = len(document_text.split())
            
            # Perform analysis components
            if self.parallel_processing:
                analysis_results = await self._run_parallel_analysis(document_text, metadata)
            else:
                analysis_results = await self._run_sequential_analysis(document_text, metadata)
            
            # Integrate results
            integrated_result = await self._integrate_analysis_results(result, analysis_results, document_text)
            
            # Generate comprehensive report
            await self._generate_analysis_report(integrated_result, analysis_results)
            
            # Cache result if enabled
            if self.enable_caching:
                self._analysis_cache[cache_key] = integrated_result
            
            # Set completion status
            integrated_result.completed_at = datetime.utcnow()
            integrated_result.processing_time = (integrated_result.completed_at - start_time).total_seconds()
            integrated_result.status = "completed"
            
            return integrated_result
            
        except Exception as e:
            result = self._create_base_result(metadata.get("document_id", "") if metadata else "")
            result.status = "failed"
            result.error_message = str(e)
            result.completed_at = datetime.utcnow()
            result.processing_time = (result.completed_at - start_time).total_seconds()
            
            if isinstance(e, (AnalysisError, ModelError, ConfigurationError)):
                raise
            else:
                raise AnalysisError(f"Document analysis failed: {str(e)}", "DocumentAnalyzer")
    
    async def _run_parallel_analysis(self, document_text: str, metadata: Optional[Dict[str, Any]]) -> Dict[str, AnalysisResult]:
        """Run all analysis components in parallel"""
        
        tasks = {}
        
        # Create analysis tasks
        if self.enable_classification and self.classifier:
            tasks["classification"] = self.classifier.analyze(document_text, metadata)
        
        if self.enable_contradiction_detection and self.contradiction_detector:
            tasks["contradiction_detection"] = self.contradiction_detector.analyze(document_text, metadata)
        
        # Execute all tasks concurrently
        completed_tasks = await asyncio.gather(*tasks.values(), return_exceptions=True)
        
        # Process results
        results = {}
        for i, (task_name, task_result) in enumerate(zip(tasks.keys(), completed_tasks)):
            if isinstance(task_result, Exception):
                # Log error but continue with other analyses
                print(f"Warning: {task_name} analysis failed: {str(task_result)}")
                results[task_name] = None
            else:
                results[task_name] = task_result
        
        # Run remedy compilation with detected issues (sequential, as it depends on other results)
        if self.enable_remedy_generation and self.remedy_compiler:
            detected_issues = []
            if results.get("contradiction_detection"):
                detected_issues.extend(results["contradiction_detection"].issues)
            
            remedy_metadata = {**(metadata or {}), "detected_issues": detected_issues}
            try:
                results["remedy_generation"] = await self.remedy_compiler.analyze(document_text, remedy_metadata)
            except Exception as e:
                print(f"Warning: Remedy generation failed: {str(e)}")
                results["remedy_generation"] = None
        
        return results
    
    async def _run_sequential_analysis(self, document_text: str, metadata: Optional[Dict[str, Any]]) -> Dict[str, AnalysisResult]:
        """Run all analysis components sequentially"""
        
        results = {}
        
        # 1. Document Classification
        if self.enable_classification and self.classifier:
            try:
                results["classification"] = await self.classifier.analyze(document_text, metadata)
            except Exception as e:
                print(f"Warning: Classification failed: {str(e)}")
                results["classification"] = None
        
        # 2. Contradiction Detection
        if self.enable_contradiction_detection and self.contradiction_detector:
            try:
                results["contradiction_detection"] = await self.contradiction_detector.analyze(document_text, metadata)
            except Exception as e:
                print(f"Warning: Contradiction detection failed: {str(e)}")
                results["contradiction_detection"] = None
        
        # 3. Remedy Generation (using detected issues)
        if self.enable_remedy_generation and self.remedy_compiler:
            detected_issues = []
            if results.get("contradiction_detection"):
                detected_issues.extend(results["contradiction_detection"].issues)
            
            remedy_metadata = {**(metadata or {}), "detected_issues": detected_issues}
            try:
                results["remedy_generation"] = await self.remedy_compiler.analyze(document_text, remedy_metadata)
            except Exception as e:
                print(f"Warning: Remedy generation failed: {str(e)}")
                results["remedy_generation"] = None
        
        return results
    
    async def _integrate_analysis_results(self, base_result: AnalysisResult, analysis_results: Dict[str, AnalysisResult], document_text: str) -> AnalysisResult:
        """Integrate results from all analysis components"""
        
        # Integrate classification results
        if analysis_results.get("classification"):
            classification_result = analysis_results["classification"]
            base_result.classification = classification_result.classification
            
            # Update confidence based on classification confidence
            if base_result.classification:
                base_result.confidence_score = max(base_result.confidence_score, base_result.classification.confidence)
        
        # Integrate contradiction detection results
        if analysis_results.get("contradiction_detection"):
            contradiction_result = analysis_results["contradiction_detection"]
            base_result.issues.extend(contradiction_result.issues)
            
            # Update confidence based on detection confidence
            if contradiction_result.confidence_score > 0:
                base_result.confidence_score = max(base_result.confidence_score, contradiction_result.confidence_score)
        
        # Integrate remedy generation results
        if analysis_results.get("remedy_generation"):
            remedy_result = analysis_results["remedy_generation"]
            base_result.remedies.extend(remedy_result.remedies)
        
        # Calculate overall confidence score
        base_result.confidence_score = self._calculate_overall_confidence(analysis_results)
        
        # Add integration metadata
        base_result.metadata.update({
            "analysis_components": {
                "classification": analysis_results.get("classification") is not None,
                "contradiction_detection": analysis_results.get("contradiction_detection") is not None,
                "remedy_generation": analysis_results.get("remedy_generation") is not None
            },
            "integration_method": "parallel" if self.parallel_processing else "sequential",
            "total_issues_found": len(base_result.issues),
            "total_remedies_suggested": len(base_result.remedies),
            "document_complexity_score": self._calculate_document_complexity(document_text)
        })
        
        return base_result
    
    async def _generate_analysis_report(self, integrated_result: AnalysisResult, analysis_results: Dict[str, AnalysisResult]) -> None:
        """Generate comprehensive analysis report"""
        
        report = {
            "executive_summary": self._generate_executive_summary(integrated_result),
            "classification_summary": self._generate_classification_summary(integrated_result.classification),
            "issues_summary": self._generate_issues_summary(integrated_result.issues),
            "remedies_summary": self._generate_remedies_summary(integrated_result.remedies),
            "risk_assessment": self._generate_risk_assessment(integrated_result.issues),
            "recommendations": self._generate_recommendations(integrated_result.remedies),
            "component_performance": {
                name: {
                    "status": "success" if result else "failed",
                    "processing_time": result.processing_time if result else None,
                    "confidence": result.confidence_score if result else None
                }
                for name, result in analysis_results.items()
            }
        }
        
        integrated_result.metadata["analysis_report"] = report
    
    def _generate_executive_summary(self, result: AnalysisResult) -> str:
        """Generate executive summary of analysis"""
        
        doc_type = result.classification.document_type.value if result.classification else "unknown"
        issues_count = len(result.issues)
        critical_issues = len([issue for issue in result.issues if issue.severity == SeverityLevel.CRITICAL])
        high_issues = len([issue for issue in result.issues if issue.severity == SeverityLevel.HIGH])
        
        summary = f"Document classified as {doc_type} with {issues_count} issues identified. "
        
        if critical_issues > 0:
            summary += f"ATTENTION REQUIRED: {critical_issues} critical issues found. "
        elif high_issues > 0:
            summary += f"{high_issues} high-priority issues require attention. "
        else:
            summary += "No critical issues identified. "
        
        remedies_count = len(result.remedies)
        if remedies_count > 0:
            summary += f"{remedies_count} remedies suggested to address identified issues."
        
        return summary
    
    def _generate_classification_summary(self, classification: Optional[Classification]) -> str:
        """Generate classification summary"""
        if not classification:
            return "Document classification unavailable."
        
        summary = f"Document type: {classification.document_type.value.title()}"
        if classification.confidence:
            summary += f" (confidence: {classification.confidence:.1%})"
        
        if classification.sub_categories:
            summary += f". Sub-categories: {', '.join(classification.sub_categories)}"
        
        return summary
    
    def _generate_issues_summary(self, issues: List[LegalIssue]) -> str:
        """Generate issues summary"""
        if not issues:
            return "No legal issues detected."
        
        by_severity = {}
        for issue in issues:
            severity = issue.severity.value
            if severity not in by_severity:
                by_severity[severity] = 0
            by_severity[severity] += 1
        
        summary_parts = []
        for severity in ["critical", "high", "medium", "low"]:
            if severity in by_severity:
                count = by_severity[severity]
                summary_parts.append(f"{count} {severity}")
        
        return f"Issues found: {', '.join(summary_parts)} priority"
    
    def _generate_remedies_summary(self, remedies: List[Remedy]) -> str:
        """Generate remedies summary"""
        if not remedies:
            return "No specific remedies suggested."
        
        categories = {}
        for remedy in remedies:
            category = remedy.category
            if category not in categories:
                categories[category] = 0
            categories[category] += 1
        
        summary = f"{len(remedies)} remedies suggested across {len(categories)} categories: "
        summary += ", ".join([f"{category} ({count})" for category, count in categories.items()])
        
        return summary
    
    def _generate_risk_assessment(self, issues: List[LegalIssue]) -> str:
        """Generate risk assessment"""
        if not issues:
            return "Low risk - no significant issues identified."
        
        critical_count = sum(1 for issue in issues if issue.severity == SeverityLevel.CRITICAL)
        high_count = sum(1 for issue in issues if issue.severity == SeverityLevel.HIGH)
        
        if critical_count > 0:
            return f"High risk - {critical_count} critical issues require immediate attention."
        elif high_count > 2:
            return f"Medium-high risk - {high_count} high-priority issues should be addressed."
        elif high_count > 0:
            return f"Medium risk - {high_count} high-priority issues identified."
        else:
            return "Low-medium risk - minor issues present but manageable."
    
    def _generate_recommendations(self, remedies: List[Remedy]) -> List[str]:
        """Generate prioritized recommendations"""
        if not remedies:
            return ["Document appears well-structured with no immediate recommendations."]
        
        # Sort remedies by priority and take top 5
        priority_order = {
            SeverityLevel.CRITICAL: 0, SeverityLevel.HIGH: 1, SeverityLevel.MEDIUM: 2,
            SeverityLevel.LOW: 3, SeverityLevel.INFO: 4
        }
        
        sorted_remedies = sorted(remedies, key=lambda r: priority_order.get(r.priority, 5))
        
        recommendations = []
        for remedy in sorted_remedies[:5]:  # Top 5 recommendations
            recommendations.append(f"{remedy.title}: {remedy.description}")
        
        return recommendations
    
    def _calculate_overall_confidence(self, analysis_results: Dict[str, AnalysisResult]) -> float:
        """Calculate overall confidence score"""
        
        confidences = []
        weights = {"classification": 0.3, "contradiction_detection": 0.4, "remedy_generation": 0.3}
        
        total_weight = 0
        weighted_confidence = 0
        
        for component, result in analysis_results.items():
            if result and result.confidence_score > 0:
                weight = weights.get(component, 0.2)
                weighted_confidence += result.confidence_score * weight
                total_weight += weight
        
        if total_weight > 0:
            return weighted_confidence / total_weight
        else:
            return 0.5  # Default confidence when no components succeeded
    
    def _calculate_document_complexity(self, document_text: str) -> float:
        """Calculate document complexity score"""
        
        # Simple complexity heuristics
        word_count = len(document_text.split())
        sentence_count = document_text.count('.') + document_text.count('!') + document_text.count('?')
        paragraph_count = len([p for p in document_text.split('\n\n') if p.strip()])
        
        # Legal language indicators
        legal_terms = ["whereas", "therefore", "hereby", "heretofore", "herein", "therein", "notwithstanding"]
        legal_term_count = sum(document_text.lower().count(term) for term in legal_terms)
        
        # Normalize scores
        word_complexity = min(1.0, word_count / 5000)  # Normalize to 5000 words
        structure_complexity = min(1.0, paragraph_count / 50)  # Normalize to 50 paragraphs
        legal_complexity = min(1.0, legal_term_count / 20)  # Normalize to 20 legal terms
        
        # Weighted average
        complexity_score = (word_complexity * 0.4 + structure_complexity * 0.3 + legal_complexity * 0.3)
        
        return complexity_score
    
    def _generate_cache_key(self, document_text: str, metadata: Optional[Dict[str, Any]]) -> str:
        """Generate cache key for analysis results"""
        import hashlib
        
        # Create hash of document text and relevant metadata
        content = document_text
        if metadata:
            # Include only relevant metadata fields for caching
            cache_metadata = {k: v for k, v in metadata.items() if k in ["document_type", "jurisdiction", "version"]}
            content += json.dumps(cache_metadata, sort_keys=True)
        
        return hashlib.md5(content.encode()).hexdigest()
    
    def get_analysis_capabilities(self) -> Dict[str, bool]:
        """Get current analysis capabilities"""
        return {
            "classification": self.enable_classification and self.classifier is not None,
            "contradiction_detection": self.enable_contradiction_detection and self.contradiction_detector is not None,
            "remedy_generation": self.enable_remedy_generation and self.remedy_compiler is not None,
            "parallel_processing": self.parallel_processing,
            "caching": self.enable_caching
        }
    
    def clear_cache(self) -> None:
        """Clear analysis results cache"""
        self._analysis_cache.clear()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "cache_size": len(self._analysis_cache),
            "cache_enabled": self.enable_caching,
            "memory_usage_mb": sum(len(str(result)) for result in self._analysis_cache.values()) / (1024 * 1024)
        }
    
    def get_version(self) -> str:
        """Get the version of this analyzer"""
        return self.VERSION