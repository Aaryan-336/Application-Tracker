import os
import sys

# Ensure backend directory is in python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.scraper_service import scraper_service
from app.services.matching_service import matching_service

def test_query_matching():
    print("Testing Keyword Matching...")
    
    # Test cases: (query, fields_list, expected_result)
    cases = [
        ("AI Engineer", ["AI/ML Research Engineer", "Develop AI algorithms"], True),
        ("Backend Engineer", ["Sales Engineer", "Selling software"], False),
        ("Go Developer", ["Senior Go Developer", "Writing Go code"], True),
        ("UI UX Designer", ["Product Designer (UI/UX)", "Design clean interfaces"], True),
        ("AI Engineer", ["Software Engineer", "No mention of intelligence"], False),
        ("", ["Any Title"], True),  # Empty query matches everything
    ]
    
    passed = 0
    for query, fields, expected in cases:
        res = scraper_service._matches_query(query, *fields)
        if res == expected:
            passed += 1
        else:
            print(f"  FAILED: query='{query}', fields={fields}, expected={expected}, got={res}")
            
    print(f"Keyword Matching: {passed}/{len(cases)} passed.")
    assert passed == len(cases)

def test_location_matching():
    print("Testing Location Matching...")
    
    # Test cases: (search_loc, job_loc, expected_result)
    cases = [
        ("Remote", "New York, NY", False),
        ("Remote", "Remote — US", True),
        ("Remote", "Worldwide", True),
        ("India", "Indianapolis, IN", False),
        ("India", "Bangalore, India", True),
        ("Bangalore", "India", True),             # City to Country expansion
        ("San Francisco", "US", True),             # SF is in US
        ("California", "San Francisco, CA", True), # CA to California abbreviation matching
        ("California", "Los Angeles, California", True),
        ("United Kingdom", "London, UK", True),    # UK country alias matching
        ("USA", "New York, NY", True),             # NY has state match, USA is alias
    ]
    
    passed = 0
    for search_loc, job_loc, expected in cases:
        res = scraper_service._matches_location(search_loc, job_loc)
        if res == expected:
            passed += 1
        else:
            print(f"  FAILED: search='{search_loc}', job='{job_loc}', expected={expected}, got={res}")
            
    print(f"Location Matching: {passed}/{len(cases)} passed.")
    assert passed == len(cases)

def test_experience_filtering():
    print("Testing Experience Level and Seniority Detection...")
    
    # Seniority Detection cases: (title, desc, expected_seniority)
    sen_cases = [
        ("Senior Lead Developer", "Looking for senior architect", "senior"),
        ("Junior Python Engineer", "0-2 years of experience", "entry"),
        ("Software Engineer", "No level mentioned", "mid"),
        ("VP of Engineering", "", "senior"),
        ("Frontend Intern", "", "entry"),
    ]
    
    passed_sen = 0
    for title, desc, expected in sen_cases:
        res = scraper_service._detect_job_seniority(title, desc)
        if res == expected:
            passed_sen += 1
        else:
            print(f"  FAILED Seniority: title='{title}', expected={expected}, got={res}")
            
    print(f"Seniority Detection: {passed_sen}/{len(sen_cases)} passed.")
    assert passed_sen == len(sen_cases)
    
    # Experience Compatibility cases: (user_level, job_level, expected_compatible)
    comp_cases = [
        ("entry", "entry", True),
        ("entry", "mid", True),
        ("entry", "senior", False),
        ("senior", "entry", False),
        ("senior", "mid", True),
        ("senior", "senior", True),
        (None, "senior", True),
    ]
    
    passed_comp = 0
    for user_l, job_l, expected in comp_cases:
        res = scraper_service._is_experience_compatible(user_l, job_l)
        if res == expected:
            passed_comp += 1
        else:
            print(f"  FAILED Compatibility: user='{user_l}', job='{job_l}', expected={expected}, got={res}")
            
    print(f"Experience Compatibility: {passed_comp}/{len(comp_cases)} passed.")
    assert passed_comp == len(comp_cases)
    
    # Score Adjustment cases: (base_score, user_level, job_level, expected_score)
    score_cases = [
        (80, "entry", "entry", 80),
        (80, "entry", "mid", 70),       # gap 1 -> penalty 10
        (80, "entry", "senior", 50),    # gap 2 -> penalty 30
        (80, "entry", "lead", 30),      # gap 3 -> penalty 50
    ]
    
    passed_score = 0
    for base, user_l, job_l, expected in score_cases:
        res = matching_service.adjust_score_for_experience(base, user_l, job_l)
        if res == expected:
            passed_score += 1
        else:
            print(f"  FAILED Score Adj: base={base}, user='{user_l}', job='{job_l}', expected={expected}, got={res}")
            
    print(f"Score Adjustment: {passed_score}/{len(score_cases)} passed.")
    assert passed_score == len(score_cases)

if __name__ == "__main__":
    print("=== RUNNING SCRAPER & MATCHING QUALITY TESTS ===")
    try:
        test_query_matching()
        test_location_matching()
        test_experience_filtering()
        print("\nALL SCRAPER QUALITY TESTS PASSED SUCCESSFULLY!")
    except AssertionError:
        sys.exit(1)
