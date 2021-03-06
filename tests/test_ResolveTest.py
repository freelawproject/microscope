from pathlib import Path
from unittest import TestCase

from eyecite import get_citations
from eyecite.models import Resource
from eyecite.resolve import resolve_citations
from eyecite.test_factories import (
    case_citation,
    id_citation,
    nonopinion_citation,
    supra_citation,
)

full1 = case_citation(0)
full2 = case_citation(1)
full3 = case_citation(4, reporter="F.2d", plaintiff="Foo", defendant="Bar")
full4 = case_citation(0, defendant="Bar")
full5 = case_citation(0, plaintiff="Ipsum")
full6 = case_citation(0, reporter="F.2d", plaintiff="Ipsum")
full7 = case_citation(0, volume="1", reporter="U.S.")
full8 = case_citation(4, reporter="F.2d", volume="2", defendant="Ipsum")
full9 = case_citation(4, reporter="F.2d", page="99", defendant="Ipsum")
full10 = case_citation(4, reporter="F.2d", plaintiff="Foo")

short1 = case_citation(0, volume="1", reporter="U.S.", short=True)
short2 = case_citation(0, antecedent_guess="Bar", short=True)
short3 = case_citation(4, reporter="F.2d", plaintiff="Foo", short=True)
short4 = case_citation(4, reporter="F.2d", defendant="wrong", short=True)
short5 = case_citation(4, reporter="F.2d", defendant="Ipsum", short=True)

supra1 = supra_citation(0, antecedent_guess="Bar")
supra2 = supra_citation(0, antecedent_guess="Ipsum")

id1 = id_citation(0)

non1 = nonopinion_citation(index=1, source_text="§99")


class ResolveTest(TestCase):
    """
    Tests whether different types of citations (i.e., full, short form,
        supra, id) are resolved properly.
    The first item in each test pair is a list of citations to resolve.
    The second item in each test pair is a dictionary of <Resource,
        List[CitationBase]> pairs.
    """

    def _assertResolution(self, citations, expected_resolution_dict):
        actual_resolution_dict = resolve_citations(citations)
        self.assertEqual(
            actual_resolution_dict,
            expected_resolution_dict,
        )

    def test_full_resolution(self):
        test_pairs = [
            # Test resolving a single, full citation
            (
                [full1],
                {Resource(full1): [full1]},
            ),
            # Test resolving two full citations to the same document
            (
                [full1, full2],
                {
                    Resource(full1): [
                        full1,
                        full2,
                    ]
                },
            ),
            # Test resolving multiple full citations to different documents
            (
                [full1, full3],
                {
                    Resource(full1): [full1],
                    Resource(full3): [full3],
                },
            ),
        ]

        for citations, resolution_dict in test_pairs:
            with self.subTest(
                "Testing citation resolution for %s..." % citations,
                citations=citations,
                resolution_dict=resolution_dict,
            ):
                self._assertResolution(citations, resolution_dict)

    def test_supra_resolution(self):
        test_pairs = [
            # Test resolving a supra citation
            (
                [full4, supra1],
                {
                    Resource(full1): [full4, supra1],
                },
            ),
            # Test resolving a supra citation when its antecedent guess matches
            # two possible candidates. We expect the supra citation to not
            # be resolved.
            (
                [full5, full6, supra2],
                {
                    Resource(full5): [full5],
                    Resource(full6): [full6],
                },
            ),
        ]

        for citations, resolution_dict in test_pairs:
            with self.subTest(
                "Testing citation resolution for %s..." % citations,
                citations=citations,
                resolution_dict=resolution_dict,
            ):
                self._assertResolution(citations, resolution_dict)

    def test_short_resolution(self):
        test_pairs = [
            # Test resolving a short form citation
            (
                [full7, short1],
                {
                    Resource(full7): [full7, short1],
                },
            ),
            # Test resolving a short form citation with an antecedent
            (
                [full4, short2],
                {
                    Resource(full4): [full4, short2],
                },
            ),
            # Test resolving a short form citation when its reporter and
            # volume match two possible candidates. We expect its antecedent
            # guess to provide the correct tiebreaker.
            (
                [full3, full8, short3],
                {
                    Resource(full3): [full3, short3],
                    Resource(full8): [full8],
                },
            ),
            # Test resolving a short form citation when its reporter and
            # volume match two possible candidates, and when it lacks a
            # meaningful antecedent. We expect the short form citation to not
            # be resolved.
            (
                [full3, full9, short4],
                {
                    Resource(full3): [full3],
                    Resource(full9): [full9],
                },
            ),
            # Test resolving a short form citation when its reporter and
            # volume match two possible candidates, and when its antecedent
            # guess also matches multiple possibilities. We expect the short
            # form citation to not be resolved.
            (
                [full6, full9, short5],
                {
                    Resource(full6): [full6],
                    Resource(full9): [full9],
                },
            ),
            # Test resolving a short form citation when its reporter and
            # volume are erroneous. We expect the short form citation to not
            # be resolved.
            (
                [full4, short4],
                {Resource(full4): [full4]},
            ),
        ]

        for citations, resolution_dict in test_pairs:
            with self.subTest(
                "Testing citation resolution for %s..." % citations,
                citations=citations,
                resolution_dict=resolution_dict,
            ):
                self._assertResolution(citations, resolution_dict)

    def test_id_resolution(self):
        test_pairs = [
            # Test resolving an Id. citation
            (
                [full4, id1],
                {Resource(full4): [full4, id1]},
            ),
            # Test resolving an Id. citation when the previous citation
            # resolution failed. We expect the Id. citation to also not be
            # resolved.
            (
                [full4, short4, id1],
                {Resource(full4): [full4]},
            ),
            # Test resolving an Id. citation when the previous citation is to a
            # non-opinion document. Since we can't resolve those documents,
            # we expect the Id. citation to also not be matched.
            (
                [full4, non1, id1],
                {Resource(full4): [full4]},
            ),
            # Test resolving an Id. citation when it is the first citation
            # found. Since there is nothing before it, we expect no matches to
            # be returned.
            ([id1], {}),
        ]

        for citations, resolution_dict in test_pairs:
            with self.subTest(
                "Testing citation resolution for %s..." % citations,
                citations=citations,
                resolution_dict=resolution_dict,
            ):
                self._assertResolution(citations, resolution_dict)

    def test_complex_resolution(self):
        """
        Tests whether resolution works with a more complex string.
        Inspired by: https://github.com/freelawproject/courtlistener/blob/d65d4c1e11328fd9f24dabd2aa9a792b4e725832/cl/citations/tests.py#L546
        """
        citation_string = (
            Path(__file__).parent / "assets" / "citation_string.txt"
        ).read_text()
        citations = get_citations(citation_string)

        self._assertResolution(
            citations,
            {
                Resource(citation=citations[0]): [
                    citations[0],
                    citations[2],
                    citations[4],
                ],
                Resource(citation=citations[1]): [
                    citations[1],
                    citations[3],
                    citations[6],
                    citations[8],
                    citations[9],
                    citations[10],
                ],
                Resource(citation=citations[5]): [citations[5], citations[12]],
            },
        )
