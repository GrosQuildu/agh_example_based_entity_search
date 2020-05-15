## Implementation of "Example Based Entity Search in the Web of Data".

```bibtex
@inproceedings{inproceedings,
    author = {Bron, Marc and Balog, Krisztian and Rijke, Maarten},
    year = {2013},
    month = {03},
    pages = {392-403},
    title = {Example Based Entity Search in the Web of Data},
    volume = {7814},
    isbn = {9783642369728},
    doi = {10.1007/978-3-642-36973-5_33}
}
```

## This tool

This tool solves a problem of searching relevant entities in [Linked Open Data](https://lod-cloud.net) (structured) graphs.

Problem statement: given relation (plain text query like "astronauts who walked on the Moon") and set of examples
(like [&lt;http://dbpedia.org/resource/Neil_Armstrong&gt;](http://dbpedia.org/resource/Neil_Armstrong) and
[&lt;http://dbpedia.org/resource/Alan_Bean&gt;](http://dbpedia.org/resource/Alan_Bean) find another, matching examples.

Problem solution is described in the paper, but the main point is to rank entities based on the probability of being
relevant to either relation (text-based approach) or examples (structured/example-based approach).
Also combination of this approaches can be used.

Tool execution looks like:
```sh
$ ebes-rank ./pp_data/ --shell
Loading triples from files in directory `./pp_data/`
Found 6 `.nq` files
-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~
Starting interactive shell
h/help - print this help
l/load - load more triples from local files
q/query - make query
s/sample - make query from sample file
e/exit - exit shell
> sample
Sample file to use: pp_data/sample1.yml
Preparing ranking for sample file
Using top 4 entities as examples
Ranking 20 entities
...
------------------------------
Ranking - text-based:
 OO http://dbpedia.org/resource/Alan_Shepard - 1
 xx http://dbpedia.org/resource/Louis_XVI_of_France - 0.8973074683334651330017202616
 xx http://dbpedia.org/resource/Odoacer - 0.8941172649739520290907284717
 OO http://dbpedia.org/resource/David_Scott - 0.8712018197108706074555150168
 OO http://dbpedia.org/resource/James_Irwin - 0.8127005405171212168537938517
~~~~~~~~~~
 R-Precision -> 0.57143
 AvgPrec -> 0.38163
------------------------------
Ranking - example-based:
 OO http://dbpedia.org/resource/Alan_Shepard - 1
 OO http://dbpedia.org/resource/Edgar_Mitchell - 0.4473684210526315789473684219
 OO http://dbpedia.org/resource/James_Irwin - 0.4210526315789473684210526322
 OO http://dbpedia.org/resource/Charles_Duke - 0.4210526315789473684210526322
 OO http://dbpedia.org/resource/David_Scott - 0.3421052631578947368421052637
~~~~~~~~~~
 R-Precision -> 0.71429
 AvgPrec -> 0.71429
------------------------------
Ranking - combined:
 OO http://dbpedia.org/resource/Alan_Shepard - 1.0
 OO http://dbpedia.org/resource/James_Irwin - 0.6168765860480342926374232419
 OO http://dbpedia.org/resource/David_Scott - 0.6066535414343826721488101402
 OO http://dbpedia.org/resource/Edgar_Mitchell - 0.5286904076387394432913215475
 xx http://dbpedia.org/resource/Louis_XVI_of_France - 0.5012853131141009875534917098
~~~~~~~~~~
 R-Precision -> 0.71429
 AvgPrec -> 0.67347

```

## Running the tool

Use `setup.py` to install scripts `ebes-data` and `ebes-rank`. 

Or run with the Docker:
```sh
git clone https://github.com/GrosQuildu/example_based_entity_search
cd example_based_entity_search
docker build -t example_based_entity_search .
docker run -it -v `pwd`/pp_data:/home/user/data example_based_entity_search
```

Commands above will mount `./pp_data` directory in the container (as `data`) and spawn interactive shell.

At the beginning, dbpedia.org endpoint is loaded. Now lets hand-craft some query:
```sh
> query
Relation (R), as plain text: most powerful sith lords
Number of examples (integer): 2
Examples (X), as URIs.
   > http://dbpedia.org/resource/Palpatine
   > http://dbpedia.org/resource/Darth_Bane
Entities to rank, as URIs. Enter (blank line) to finish:
   > http://dbpedia.org/resource/Darth_Vader
   > http://dbpedia.org/resource/Darth_Maul
   > http://dbpedia.org/resource/Revan
   > http://dbpedia.org/resource/Sauron
   > http://dbpedia.org/resource/Yoda
   > http://dbpedia.org/resource/Qui-Gon_Jinn
   > http://dbpedia.org/resource/Mace_Windu
   > http://dbpedia.org/resource/Obi-Wan_Kenobi
   > http://dbpedia.org/resource/James_Bond
   > http://dbpedia.org/resource/G._K._Chesterton
   > 
Ranking 10 entities
 ~> ranking entity no 0 / 10
...
Ranking - text-based:
 OO http://dbpedia.org/resource/Darth_Vader - 1
 OO http://dbpedia.org/resource/Revan - 0.9941088851845064208453746594
 OO http://dbpedia.org/resource/Darth_Maul - 0.9271692750255459152127209907
 xx http://dbpedia.org/resource/Mace_Windu - 0.5053067699988764603154636999
 xx http://dbpedia.org/resource/James_Bond - 0.1769364793649063167785469810
 xx http://dbpedia.org/resource/Obi-Wan_Kenobi - 0.1574433650187221333035511766
 xx http://dbpedia.org/resource/Qui-Gon_Jinn - 0.1166633054001528293587669988
 xx http://dbpedia.org/resource/Yoda - 0.05259709003653568294731773713
 xx http://dbpedia.org/resource/Sauron - 0.002722182115243205931012787568
 xx http://dbpedia.org/resource/G._K._Chesterton - 0.0
~~~~~~~~~~
 R-Precision -> 1.00000
 AvgPrec -> 1.00000
------------------------------
Ranking - example-based:
 xx http://dbpedia.org/resource/Yoda - 1
 xx http://dbpedia.org/resource/Qui-Gon_Jinn - 0.9999999999999999999999999997
 xx http://dbpedia.org/resource/Obi-Wan_Kenobi - 0.9999999999999999999999999997
 xx http://dbpedia.org/resource/Mace_Windu - 0.9999999999999999999999999997
 OO http://dbpedia.org/resource/Darth_Vader - 0.9999999999999999999999999997
 OO http://dbpedia.org/resource/Darth_Maul - 0.5714285714285714285714285713
 OO http://dbpedia.org/resource/Revan - 0.4285714285714285714285714286
 xx http://dbpedia.org/resource/Sauron - 0.1428571428571428571428571429
 xx http://dbpedia.org/resource/G._K._Chesterton - 0.1428571428571428571428571429
 xx http://dbpedia.org/resource/James_Bond - 0E+30
~~~~~~~~~~
 R-Precision -> 0.00000
 AvgPrec -> 0.00000
------------------------------
Ranking - combined:
 OO http://dbpedia.org/resource/Darth_Vader - 0.9999999999999999999999999998
 xx http://dbpedia.org/resource/Mace_Windu - 0.7526533849994382301577318498
 OO http://dbpedia.org/resource/Darth_Maul - 0.7492989232270586718920747810
 OO http://dbpedia.org/resource/Revan - 0.7113401568779674961369730440
 xx http://dbpedia.org/resource/Obi-Wan_Kenobi - 0.5787216825093610666517755881
 xx http://dbpedia.org/resource/Qui-Gon_Jinn - 0.5583316527000764146793834992
 xx http://dbpedia.org/resource/Yoda - 0.5262985450182678414736588686
 xx http://dbpedia.org/resource/James_Bond - 0.08846823968245315838927349050
 xx http://dbpedia.org/resource/Sauron - 0.07278966248619303153693496523
 xx http://dbpedia.org/resource/G._K._Chesterton - 0.07142857142857142857142857145
~~~~~~~~~~
 R-Precision -> 0.66667
 AvgPrec -> 0.55556
```

It is pretty slow, because we need to do a lot of HTTP requests.
If you have a file with RDF triples you may use it instead. Run `load` command:
```sh
> load
Path to triples file or SPARQL endpoint url: data/sample5.nq
Loading triples from file `data/sample5.nq`
Switching PPGraph backend from remote endpoint to local files
```

Now, instead of writing query from nothing, execute ready query from a sample file:
```sh
> sample
Sample file to use: data/sample5.yml
Preparing ranking for sample file `data/sample5.yml`
Ranking 16 entities
 ~> ranking entity no 0 / 16
...
```

If you don't have RDF file but want one, appropriate to a sample file, then use `ebes-data` (`dump_data.py`) script:
```sh
ebes-data -v pp_data/out.nq ./pp_data/sample1.yml not_relevant
# or
chmod a+w pp_data
docker run -it -v `pwd`/pp_data:/home/user/data example_based_entity_search \
       ebes-data -v data/out.nq ./data/sample1.yml relevant
```

To evaluate the tool on multiple triples files and samples, run `evaluate.py` script:
```sh
$ python ./example_based_entity_search/evaluate.py ./pp_data
Loading graphs...
...
Mean stats:
  Ranking with `text-based` method
    Mean-R-Precision -> 0.25397
    Mean-AvgPrec -> 0.19444
  Ranking with `examples-based` method
    Mean-R-Precision -> 0.62937
    Mean-AvgPrec -> 0.59862
  Ranking with `combined-based` method
    Mean-R-Precision -> 0.71667
    Mean-AvgPrec -> 0.66728
```

## Data
#### Original
The base graph of structured data used in the paper was BTC-2009:

  * link: http://km.aifb.kit.edu/projects/btc-2009/
    
  * format: n-quads, plaintext file with triple+grap on every line, like:
    `<http://one.example/subject1> <http://one.example/predicate1 <http://one.example/object1> <http://example.org/graph3> .`
    
  * size: 17GiB, or 2.2GiB for testing

For queries (relations/topics and examples) three sets were used:

  * SemSearch'11
  
      * topics
          * link: http://km.aifb.kit.edu/ws/semsearch10/Files/samplequeries-list
          * full list (50 topics) is not available
      * examples
          * evaluation data (qrels) as URIs was used as examples, but is not available

  * INEX’07 and INEX’08
    
      * '07 and '08 not available, newer are though
      * link: https://inex.mmci.uni-saarland.de/data/documentcollection.html#lod
      * topics: a lot of them
      * examples
          * as qrels to wikipedia pages
          * semi-manuall mapping between pages and dbpedia URIs was done in the paper

#### Local

Topics and relevant data used in the paper are not accessible. I have manually forged some samples,
look for `.yml` files inside `pp_data` directory. As a base graph I used [dbpedia.org](https://dbpedia.org/sparql).
Triples relevant to samples can be found in `pp_data/*.nq` files. 

#### Structure of data for this tools 

To rank entities we need two things: triples graph (SemWeb data) and sample (query).

Triples graph can be parsed from a file in any format supported by rdflib
(RDF/XML, N3, NTriples, N-Quads, Turtle, TriX, RDFa and Microdata). Or remote SPARQL endpoint can be used.

Query should be stored in a [YAML](https://yaml.org/) file with the following format:

```yaml

---
topic: astronauts who walked on the Moon  # plain text relation
examples: 1  # use this number of top relevant entities as examples
relevant:  # examples and entities known to be relevant
    - http://dbpedia.org/resource/Neil_Armstrong
    - http://dbpedia.org/resource/Alan_Bean
not_relevant:  # entities known to be not relevant
    - http://dbpedia.org/resource/Samuel_Beckett
...
```

For "real" queries number of `relevant` entities would be equal to `examples` and `not_relevant`
entities would be a list of all examples we want to rank.

Note that the graph used should contain some triples related to every entity specified the query.
So either use remote endpoint (which is slow but trustworthy) or make sure that RDF file you use
contains necessary information. Possibly use `dump_data.py` (`ebes-data`) script for data acquisition. 

## Remarks
* General

    * I couldn't find a parser for data used in the paper (BTC-2009) efficient enough to be usable. 
    Both [rdflib](https://github.com/RDFLib/rdflib) (in python) and [Redland librdf](http://librdf.org/)
    (in C with python bindings) were tested. Because of that I used remote [dbpedia.org](https://dbpedia.org/sparql)
    endpoint as a data collection and have dumped relevant triples from it. 

    * The paper rank entities by computing "fitness" probability for every entity.
    But computing such probability for every known subject node seem impractical, as there are a lot of them.
    For example: dbpedia.org contains few millions entities, if processing one entity takes 0.1 sec,
    then processing one user query would take about a week. Don't know how this problem should be tackled nor
    how it was solved in the paper. I just assume that user provides all entities (probably both relevant and
    not-relevant) that should be ranked.
    
    * No way to return correct amount of matching examples. For example when query says `ten ancient Greek city`
    we can't handle this `ten`.   

    * Text-based probabilities are products of partial probabilities and therefore are small.
    This may lead to precision errors (somehow solved with python's `Decimal` module) and is not compatible with example-based approach, which produces much higher probabilities. This problem is not mentioned in the paper. I have applied min-max normalization.
    
    * Parameters in combined approach are tailored to test data in the paper. Reason: comparison of tex and structured approaches under "ideal" conditions. Dunno how to set the params in real word queries. Also computing average precision using examples is not well described, f.e. how assumed amount of relevant entities was set.  

* Text-based approach

  * Dirichlet smoothing part of equations was poorly described in the paper.
  It is uncertain how "Dirichlet smoothed model of the entire collection of triples" (probability P(t|theta_c))
  should be computed. Following standard approach (described in other resources) would require to iterate over
  all triples for every term in the relation, which is computationally expensive. Moreover, it would require
  every term to appear at least once in the collection, so as the probability won't be zero.
  Such requirement seems not to be stated in the paper. Also parameter `ni` was not provided.
  
  In the implementation I used a simplified version of Dirichlet model.
  Nominator part is set to 1 and `ni` parameter to number of known entities (amount of subjects in the graph).

* Example-based approach

  * Representing an entity as a set of inlink/outlink triples doesn't make much sense for triples
   in which an object is Literal, because such triple won't match any other entity for sure.
   It is (intuitively) better to Nullify subjects in such triples.
   For example: 
      ```
      Entity A representation:
        A -> y -> v (A1), outlink
        A -> x -> B (A2), outlink

      Entity B representation:
        B -> y -> v (B1), outlink
        A -> x -> B (B2), inlink
      ```
    Only `A2-B2` matches. But if:
      ```
      Entity A representation:
        None -> y -> v (A1), outlink
        A -> x -> B (A2), outlink

      Entity B representation:
        None -> y -> v (B1), outlink
        A -> x -> B (B2), inlink
      ```
    Then both `A1-B2` and `A2-B2` match!
 