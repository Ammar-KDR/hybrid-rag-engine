from .model import Claim , CitationVerificationResult


class CitationVerificationRunner:

    def __init__(self, verifier):
        self.verifier = verifier

    def run(
        self,
        claims: list[Claim],
        evidence_by_reference: dict[int, str],
    ) -> CitationVerificationResult:
        
        verifications = []
        uncited_claims = []
        unresolved_references = []
        for claim in claims:
            if len(claim.citations) ==0:
                uncited_claims.append(claim)
            else:
                for citation in claim.citations:
                    if citation not in evidence_by_reference :

                        if citation not in unresolved_references:
                            unresolved_references.append(citation)
                        
                    else:
                        verifications.append(self.verifier.verify(claim,citation,evidence_by_reference[citation]))
        
        return CitationVerificationResult(
            verifications=verifications,
            uncited_claims=uncited_claims,
            unresolved_references=unresolved_references
        )

        

                        

