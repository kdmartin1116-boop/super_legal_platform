from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List, Optional
from slowapi import Limiter
from slowapi.util import get_remote_address

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.get("/modules")
async def get_education_modules():
    """Get available education modules"""
    
    modules = {
        "communication_skills": {
            "id": "communication_skills",
            "name": "Communication Skills Training",
            "description": "Improve professional communication and word choices",
            "lessons": [
                {
                    "id": "effective_writing",
                    "title": "Effective Written Communication",
                    "duration": 30,
                    "topics": ["Clarity", "Conciseness", "Professional tone"]
                },
                {
                    "id": "legal_correspondence", 
                    "title": "Legal Correspondence",
                    "duration": 45,
                    "topics": ["Formal letters", "Legal language", "Proper formatting"]
                },
                {
                    "id": "negotiation_skills",
                    "title": "Negotiation and Persuasion",
                    "duration": 60,
                    "topics": ["Persuasive writing", "Negotiation tactics", "Conflict resolution"]
                }
            ],
            "total_lessons": 3,
            "estimated_completion": "2-3 hours"
        },
        "legal_terminology": {
            "id": "legal_terminology",
            "name": "Legal Terminology Dictionary",
            "description": "Comprehensive legal terms from multiple jurisdictions",
            "categories": [
                {
                    "id": "constitutional_law",
                    "name": "Constitutional Law",
                    "term_count": 150,
                    "description": "Fundamental constitutional principles and terminology"
                },
                {
                    "id": "commercial_law",
                    "name": "Commercial Law", 
                    "term_count": 200,
                    "description": "UCC, contracts, and commercial transactions"
                },
                {
                    "id": "civil_procedure",
                    "name": "Civil Procedure",
                    "term_count": 180,
                    "description": "Court procedures and civil litigation terms"
                },
                {
                    "id": "consumer_protection",
                    "name": "Consumer Protection",
                    "term_count": 120,
                    "description": "FDCPA, FCRA, TILA, and consumer rights"
                }
            ],
            "total_terms": 650,
            "jurisdictions": ["Federal", "State", "Common Law"]
        }
    }
    
    return {"modules": modules}


@router.get("/legal-terms")
async def search_legal_terms(
    query: Optional[str] = None,
    category: Optional[str] = None,
    jurisdiction: Optional[str] = None
):
    """Search legal terminology database"""
    
    # Sample legal terms (would come from database in production)
    sample_terms = [
        {
            "term": "Affidavit",
            "definition": "A written statement of facts confirmed by oath or affirmation of the party making it, taken before a person having authority to administer such oath or affirmation.",
            "category": "civil_procedure",
            "jurisdiction": "Federal",
            "usage_example": "The plaintiff filed an affidavit of truth supporting their motion.",
            "related_terms": ["Declaration", "Oath", "Affirmation", "Sworn statement"],
            "legal_citations": ["Fed. R. Civ. P. 56(c)(4)", "28 U.S.C. § 1746"]
        },
        {
            "term": "Negotiable Instrument", 
            "definition": "A signed document that promises a sum of payment to a specified person or the assignee, containing certain characteristics that make it transferable.",
            "category": "commercial_law",
            "jurisdiction": "Federal",
            "usage_example": "The promissory note qualified as a negotiable instrument under UCC Article 3.",
            "related_terms": ["UCC 3-104", "Bearer instrument", "Order instrument", "Endorsement"],
            "legal_citations": ["UCC § 3-104", "UCC § 3-201"]
        },
        {
            "term": "State National",
            "definition": "A person born in and subject to the jurisdiction of the United States who owes allegiance to the United States but is not a citizen under the 14th Amendment.",
            "category": "constitutional_law", 
            "jurisdiction": "Federal",
            "usage_example": "Under 8 USC § 1101(a)(21), a state national may obtain a passport.",
            "related_terms": ["Non-citizen national", "Citizenship", "14th Amendment", "Natural born"],
            "legal_citations": ["8 USC § 1101(a)(21)", "8 USC § 1408"]
        },
        {
            "term": "Fair Debt Collection Practices Act",
            "definition": "Federal law that limits the behavior and actions of third-party debt collectors who are attempting to collect debts on behalf of another person or entity.",
            "category": "consumer_protection",
            "jurisdiction": "Federal", 
            "usage_example": "The debt collector violated FDCPA by calling outside permitted hours.",
            "related_terms": ["Debt collector", "Consumer", "Harassment", "Validation notice"],
            "legal_citations": ["15 USC § 1692 et seq.", "CFPB Regulation F"]
        }
    ]
    
    # Filter results based on query parameters
    results = sample_terms
    
    if query:
        query_lower = query.lower()
        results = [
            term for term in results 
            if query_lower in term['term'].lower() or 
               query_lower in term['definition'].lower()
        ]
    
    if category:
        results = [term for term in results if term['category'] == category]
    
    if jurisdiction:
        results = [term for term in results if term['jurisdiction'] == jurisdiction]
    
    return {
        "query": query,
        "filters": {"category": category, "jurisdiction": jurisdiction},
        "total_results": len(results),
        "terms": results
    }


@router.get("/lesson/{lesson_id}")
async def get_lesson_content(lesson_id: str):
    """Get specific lesson content"""
    
    lessons = {
        "effective_writing": {
            "id": "effective_writing",
            "title": "Effective Written Communication",
            "description": "Master the fundamentals of clear, professional writing",
            "duration": 30,
            "content": {
                "introduction": "Effective communication is essential for legal and business success.",
                "sections": [
                    {
                        "title": "Clarity and Precision",
                        "content": "Use clear, specific language. Avoid ambiguity that could be misinterpreted.",
                        "examples": [
                            {
                                "poor": "We request that you handle this matter.",
                                "better": "Please respond to this dispute within 30 days as required by 15 USC § 1692g."
                            }
                        ]
                    },
                    {
                        "title": "Professional Tone",
                        "content": "Maintain a respectful but firm tone in all correspondence.",
                        "examples": [
                            {
                                "poor": "You guys better fix this mess immediately!",
                                "better": "We respectfully request immediate correction of these inaccuracies."
                            }
                        ]
                    },
                    {
                        "title": "Legal Language Integration",
                        "content": "Incorporate appropriate legal terms while maintaining readability.",
                        "examples": [
                            {
                                "casual": "This doesn't seem right to me.",
                                "professional": "This practice appears to violate the Fair Credit Reporting Act, specifically 15 USC § 1681e(b)."
                            }
                        ]
                    }
                ],
                "exercises": [
                    {
                        "type": "rewrite",
                        "instruction": "Rewrite the following sentence for clarity and professionalism:",
                        "text": "Your company keeps bugging me about money I don't think I owe.",
                        "answer": "Your company's repeated collection attempts regarding this disputed debt may violate the Fair Debt Collection Practices Act."
                    }
                ]
            },
            "quiz": [
                {
                    "question": "Which approach is most effective for legal correspondence?",
                    "options": [
                        "Emotional appeals and personal stories",
                        "Clear facts with relevant legal citations", 
                        "Aggressive language to show seriousness",
                        "Casual tone to build rapport"
                    ],
                    "correct": 1,
                    "explanation": "Legal correspondence should be factual, professional, and cite relevant authorities."
                }
            ]
        }
    }
    
    if lesson_id not in lessons:
        raise HTTPException(status_code=404, detail="Lesson not found")
    
    return lessons[lesson_id]


@router.post("/progress")
@limiter.limit("50/hour")
async def update_progress(progress_data: Dict[str, Any]):
    """Update user's education progress"""
    
    # This would integrate with user authentication and database
    return {
        "success": True,
        "message": "Progress updated successfully",
        "updated_progress": progress_data
    }


@router.get("/progress/{user_id}")
async def get_user_progress(user_id: str):
    """Get user's education progress"""
    
    # Sample progress data (would come from database)
    progress = {
        "user_id": user_id,
        "modules": {
            "communication_skills": {
                "completed_lessons": 2,
                "total_lessons": 3,
                "completion_percentage": 67,
                "time_spent": 75,  # minutes
                "last_accessed": "2025-10-23T14:30:00Z"
            },
            "legal_terminology": {
                "terms_learned": 45,
                "total_terms": 650,
                "completion_percentage": 7,
                "time_spent": 120,  # minutes
                "last_accessed": "2025-10-24T09:15:00Z"
            }
        },
        "achievements": [
            {
                "id": "first_lesson",
                "name": "Getting Started",
                "description": "Completed your first lesson",
                "earned_date": "2025-10-20T16:45:00Z"
            },
            {
                "id": "communication_beginner",
                "name": "Communication Novice", 
                "description": "Completed 2 communication lessons",
                "earned_date": "2025-10-23T14:30:00Z"
            }
        ],
        "overall_stats": {
            "total_time_spent": 195,  # minutes
            "lessons_completed": 2,
            "terms_mastered": 45,
            "streak_days": 4
        }
    }
    
    return progress