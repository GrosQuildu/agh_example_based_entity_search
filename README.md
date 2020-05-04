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
Also combination of this approaches was proposed.

Tool execution looks like:
```sh
$ ebes-rank ./pp_data/ --shell
Loading triples from files in directory `./pp_data/`
Found 5 `.nq` files
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
Ranking 20 entities
...
------------------------------
Ranking - text-based:
 OK http://dbpedia.org/resource/Buzz_Aldrin - 8.403523093400763812246367990E-30
 OK http://dbpedia.org/resource/Harrison_Schmitt - 6.341459520844494029874975429E-30
 OK http://dbpedia.org/resource/Neil_Armstrong - 3.853314213149515399003529054E-30
 OK http://dbpedia.org/resource/Alan_Shepard - 3.182195457936311474102390319E-30
 NO http://dbpedia.org/resource/Louis_XVI_of_France - 2.855930219419808238422461393E-30
 NO http://dbpedia.org/resource/Odoacer - 2.847910451500284397485284457E-30
 NO http://dbpedia.org/resource/Harry_Potter - 2.080013520648365938729348544E-30
 OK http://dbpedia.org/resource/Charles_Duke - 1.211139645598227351159427758E-30
 NO http://dbpedia.org/resource/Samuel_Beckett - 5.132920069928481291855411872E-31
 NO http://dbpedia.org/resource/Chaz_Bono - 3.166097541652364891122272746E-31
 NO http://dbpedia.org/resource/Brad_Pitt - 2.312952965173047858611960955E-31
 NO http://dbpedia.org/resource/Menelaus - 1.699779542314832638553178478E-31
 NO http://dbpedia.org/resource/Gero_von_Wilpert - 1.483207159209379175098285078E-31
 NO http://dbpedia.org/resource/Cameron_Diaz - 1.463174421742162322936943486E-31
 NO http://dbpedia.org/resource/Bolesław_Leśmian - 7.662270280768847858922275770E-32
 NO http://dbpedia.org/resource/Edward_Thomas_(poet) - 7.644492007044185460333287629E-32
 NO http://dbpedia.org/resource/Edmund_Rich - 7.550239209520260932104305842E-32
 NO http://dbpedia.org/resource/Pope_Leo_VIII - 5.116978826336706868394768505E-32
 OK http://dbpedia.org/resource/Gene_Cernan - 1.427739517906317019845690401E-32
 OK http://dbpedia.org/resource/John_Young - 1.421946338029700446985601333E-32
------------------------------
Ranking - example-based:
 OK http://dbpedia.org/resource/Buzz_Aldrin - 0.1669154971633323380113466732
 OK http://dbpedia.org/resource/Alan_Shepard - 0.1630337414153478650343386106
 OK http://dbpedia.org/resource/Neil_Armstrong - 0.1537772469393848910122424631
 OK http://dbpedia.org/resource/Charles_Duke - 0.1475067184234099731263063610
 OK http://dbpedia.org/resource/Harrison_Schmitt - 0.09405792773962376828904150500
 NO http://dbpedia.org/resource/Edward_Thomas_(poet) - 0.03493580173186025679307255896
 NO http://dbpedia.org/resource/Brad_Pitt - 0.03194983577187220065691251122
 NO http://dbpedia.org/resource/Chaz_Bono - 0.03165123917587339504329650644
 NO http://dbpedia.org/resource/Samuel_Beckett - 0.03135264257987458942968050166
 NO http://dbpedia.org/resource/Cameron_Diaz - 0.03015825619587936697521648255
 NO http://dbpedia.org/resource/Gero_von_Wilpert - 0.02896386981188414452075246342
 NO http://dbpedia.org/resource/Odoacer - 0.02866527321588533890713645864
 NO http://dbpedia.org/resource/Louis_XVI_of_France - 0.02776948342788892206628844431
 NO http://dbpedia.org/resource/Edmund_Rich - 0.02657509704389369961182442520
 NO http://dbpedia.org/resource/Pope_Leo_VIII - 0.02478351746790086593012839653
 NO http://dbpedia.org/resource/Bolesław_Leśmian - 0.02448492087190206031651239176
 NO http://dbpedia.org/resource/Menelaus - 0.02388772767990444908928038220
 NO http://dbpedia.org/resource/Harry_Potter - 0.006569125111973723499552105106
 OK http://dbpedia.org/resource/Gene_Cernan - 0.006270528515974917885936100328
 OK http://dbpedia.org/resource/John_Young - 0
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
------------------------------
Ranking - text-based:
 http://dbpedia.org/resource/Darth_Vader - 1.405558168120405905088125607E-16
 http://dbpedia.org/resource/Revan - 1.398970640143771268550264186E-16
 http://dbpedia.org/resource/Darth_Maul - 1.324117820519982851698630489E-16
 http://dbpedia.org/resource/Mace_Windu - 8.523851958480738507552716070E-17
 http://dbpedia.org/resource/James_Bond - 4.851968887117295073021727182E-17
 http://dbpedia.org/resource/Obi-Wan_Kenobi - 4.633994123207575686367693457E-17
 http://dbpedia.org/resource/Qui-Gon_Jinn - 4.177985724050877073177547586E-17
 http://dbpedia.org/resource/Yoda - 3.461588235149503761620056721E-17
 http://dbpedia.org/resource/Sauron - 2.903879954877150388445926839E-17
 http://dbpedia.org/resource/G._K._Chesterton - 2.873440129133987334846882730E-17
------------------------------
Ranking - example-based:
 http://dbpedia.org/resource/Darth_Vader - 0.3197353914002205071664829098
 http://dbpedia.org/resource/Obi-Wan_Kenobi - 0.2149944873208379272326350602
 http://dbpedia.org/resource/Yoda - 0.1797133406835722160970231530
 http://dbpedia.org/resource/Mace_Windu - 0.1543550165380374862183020947
 http://dbpedia.org/resource/Darth_Maul - 0.1543550165380374862183020947
 http://dbpedia.org/resource/Qui-Gon_Jinn - 0.1356119073869900771775082689
 http://dbpedia.org/resource/Revan - 0.08489525909592061742006615223
 http://dbpedia.org/resource/Sauron - 0.04410143329658213891951488434
 http://dbpedia.org/resource/G._K._Chesterton - 0.03528114663726571113561190740
 http://dbpedia.org/resource/James_Bond - 0.03087100330760749724366041903
```

It is pretty slow, because we need to do a lot of HTTP queries.
If you have a file with RDF triples you may use it instead. Run `load` command:
```sh
> load
Path to triples file or SPARQL endpoint url: data/sample1.nq
Loading triples from file `data/sample1.nq`
Switching PPGraph backend from remote endpoint to local files
```

Now, instead of writing query from nothing, execute ready query from a sample file:
```sh
> sample
Sample file to use: data/sample1.yml
Preparing ranking for sample file `data/sample1.yml`
Ranking 20 entities
 ~> ranking entity no 0 / 20
...
```

If you don't have RDF file but want one, appropriate to a sample file, then use `ebes-data` (`dump_data.py`) script:
```sh
ebes-data -v pp_data/out.nq ./pp_data/sample1.yml not_relevant
# or
docker run -it -v `pwd`/pp_data:/home/user/data example_based_entity_search \
       ebes-data -v data/out.nq ./data/sample1.yml relevant
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
    
* Text-based approach

  * Dirichlet smoothing part of equations was poorly described in the paper.
  It is uncertain how "Dirichlet smoothed model of the entire collection of triples" (probability P(t|theta_c))
  should be computed. Following standard approach (described in other resources) would require to iterate over
  all triples for every term in the relation, which is computationally expensive. Moreover, it would require
  every term to appear at least once in the collection, so as the probability won't be zero.
  Such requirement seems not to be stated in the paper. Also parameter `ni` was not provided.
  
  In the implementation I used a simplified version of Dirichlet model.
  Nominator part is set to 1 and `ni` parameter to number of known entities (amount of subjects in the graph).

  * Final probabilities are products of partial probabilities and therefore are small.
  This may lead to precision errors (somehow solved with python's `Decimal` module) and is not compatible with
  example-based approach (which produces much higher probabilities). This problem is not mentioned in the paper.

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
 