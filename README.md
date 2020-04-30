The base blob of structured data is BTC-2009:
    link: http://km.aifb.kit.edu/projects/btc-2009/
    format: n-quads, plaintext file with triple+grap on every line, like:
    <http://one.example/subject1> <http://one.example/predicate1 <http://one.example/object1> <http://example.org/graph3>.
    size: 17GiB, or 2,2GiB for testing

For queries (relations/topics and examples) three sets were used:
    SemSearch'11
        topics
            link: http://km.aifb.kit.edu/ws/semsearch10/Files/samplequeries-list
            full list (50 topics) is not available
        examples
            evaluation data (qrels) as URIs was used as examples, but is not available

    INEX’07 and INEX’08
        '07 and '08 not available, newer are though
        link: https://inex.mmci.uni-saarland.de/data/documentcollection.html#lod
        topics
            a lot of them
        examples
            as qrels to wikipedia pages
            semi-manuall mapping between pages and dbpedia URIs was done in the paper

Problems and remarks:

* Data

    - I couldn't find parser for data used in the paper (BTC-2009) efficient enough to be usable. Both rdflib (in python) and Redland librdf (in C with python bindings) were tested. Because of that I used remote dbpedia.org enpoint as a data collection.

    - Topics and relevant data used in the paper are not accessible. I manually forged such data.

    - The paper rank entities by computing "fitness" probability for every entity. But computing such probability for every known subject node seem impractical, as ther are a lot of them. For example: dbpedia.org contains few millions entities, if processing one entity takes 0.1 sec, then processing one user query would take about a week. Don't know how this problem should be tackled.

* Text-based approach

    - Dirichlet smoothing part of equations was poorly described in the paper. It is uncertain how "Dirichlet smoothed model of the entire collection of triples" (probability P(t|theta_c)) should be computed. Following standard approach (described in other resources) would require to iterate over all triples for every term in the relation, which is computationally expensive. Moreover, it would require every term to appear at least once in the collection, so as the probability won't be zero. Such requirement seems not to be stated in the paper.
    Also parameter `ni` was not provided
    In the implementation I used a simplified version of Dirichlet model.

    - Final probabilities are products of partial probabilities and therefore are small and prone to precision errors

    - Probabilities are based on number of occurrences of a term in the text representation of an entity divided by size of the representation. But number of occurrences is relatively small compared to the size, for both relevant and not relevant entities. So ranking is biased by the size of text representation.
    For example probabilities for term "moon":
        For entity "Neil_Armstrong":
            -> probability for attributes: 0.00937 (tf=3, |e|=421)
            -> probability for types: 0.01316 (tf=0, |e|=70)
            -> probability for links: 0.02128 (tf=0, |e|=41)
            -> term probability: 0.01445

        For entity "Harry_Potter":
            -> probability for attributes: 0.00287 (tf=0, |e|=342)
            -> probability for types: 0.05263 (tf=0, |e|=13)
            -> probability for links: 0.02632 (tf=0, |e|=32)
            -> term probability: 0.02700

    The probabilities are roughly equal to tf/|e|. As can be seen, moon is more relevant term for the wizard than for the astronaut. Despite the fact that it appears in the astronaut text representation more times.


