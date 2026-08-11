from backend.app.generation.citation_validator import validate, extract_markers, is_exact_refusal

def test_citation_validator():
    sources = [{"marker": 1}, {"marker": 2}, {"marker": 3}]
    
    # 1. Valid cited answer
    res = validate("Taxpayers have the right to retain representation [1].", sources)
    assert res["grounded"] == True, f"Failed case 1: {res}"
    
    # 2. Missing citation
    res = validate("Taxpayers have the right to retain representation.", sources)
    assert res["grounded"] == False, f"Failed case 2: {res}"
    assert "without providing a citation" in res["problem"], f"Failed case 2 msg: {res}"
    
    # 3. Fabricated marker
    res = validate("Taxpayers have this right [99].", sources)
    assert res["grounded"] == False, f"Failed case 3: {res}"
    assert "99" in res["problem"], f"Failed case 3 msg: {res}"
    
    # 4. Valid refusal
    res = validate("I could not find the answer in the provided legal sources.", sources)
    assert res["grounded"] == True, f"Failed case 4: {res}"
    assert res["is_refusal"] == True, f"Failed case 4 refusal: {res}"
    
    # 5. Invalid refusal with extra unsupported claims
    res = validate("I could not find the answer in the provided legal sources. However, generally...", sources)
    assert res["grounded"] == False, f"Failed case 5: {res}"
    assert res["is_refusal"] == False, f"Failed case 5 refusal: {res}"

if __name__ == "__main__":
    test_citation_validator()
    print("All citation validator tests passed!")
