# PROJECT IDEA: SEMANTIC SEARCH VECTOR DATABASE + MCP SERVER + MORE

What I'd like to create is a project that is capable of running both locally (through CLI) and as an MCP server for semantic search for a library of different books, articles, essays, and other text items. This will partly be used to organized my books and readings.

I'd like to set it up at different granularities, at the chapter level, at the subsection level, at the semantic chunk level; This means chunked but semantically, meaning each chunk is somewhat semantically self-contained and so there aren't abrupt divisions between chunks, and if one were to do a lookup and get a particular chunk and themselves read it, they should have a basic grasp of what is being understood.

Ideally we would be able to have different relations between chunks or larger text elements and have those relations be specified, whether that is a reference relation (is cited by, cites) or a genealogical relation (this is a development of this idea express in this other chunk / text element) or internal to a book some development of the thesis or argument. Another relationship could be is_contained_in and is_contained_by, which would be the relationship between a book (level 0) and its parts or chapters, parts (level 1) and their chapters or sections, chapters (level 2) and their sections or sub-sections, sections (level 3) and their sub-sections etc. With respect to each text_element being an element of the database, only the leaves of the containment tree will have the actual text but obviously we can easily get the text for a book by traversing the tree of text_elements that is contained in it. 

 This is obviously a non-exhaustive list of the potential relationships and our system must be capable of introducing new relationships. Some other relationships could be:

## Conceptual Relationships
- **defines/is_defined_by** - Track where concepts are formally defined vs. where they're used
- **contradicts/is_contradicted_by** - Opposing philosophical positions
- **extends/is_extended_by** - One text building upon another's concepts
- **critiques/is_critiqued_by** - Critical engagement with ideas

## Historical Relationships
- **precedes/follows** - Temporal relationships in intellectual history
- **responds_to/is_responded_to_by** - Direct philosophical responses
- **influenced/is_influenced_by** - Intellectual heritage relationships

## School/Tradition Relationships
- **belongs_to_school** - Associate text with philosophical traditions (Existentialism, Analytic, etc.)
- **revises/is_revised_by** - Updates to philosophical positions within traditions
- **canonical/non-canonical** - Status within a philosophical tradition

## Methodological Relationships
- **applies_method_of** - Shared philosophical approaches
- **introduces_methodology** - Novel philosophical methods

## Dialog Relationships
- **in_dialog_with** - Texts engaged in implicit conversation
- **synthesizes** - Texts that combine multiple perspectives

## Thematic Relationships
- **explores_theme** - Connect texts by philosophical themes (ethics, metaphysics, etc.)
- **central_to/peripheral_to** - Relevance to specific philosophical debates

These relationships could be implemented in PostgreSQL using either a dedicated relationships table with relationship_type as an enum field, or as separate relationship-specific tables for more complex metadata.

Now I want to compartmentalize how these searches can be specified, for example, if someone wants to search for something in Hegelian Philosophy (say where Hegel speaks about the concept of Being), I'd like to perhaps narrow the search down to that. Or perhaps I want to just search all the readings from my class PHL316. Or perhaps I want to search something from "the first half of the semester", or from a specific week. The search should be able to narrow that down. 

This database won't just be useful for search through, it might also very well be useful for discovery by other means such as various types of inferences:

## Types of Inference Possible

1. **Transitive Relationship Inference**
   - If text A influences text B, and B influences C, infer A indirectly influences C
   - Implemented using recursive Common Table Expressions (CTEs)

2. **Inverse Relationship Maintenance**
   - Automatically create bidirectional relationships (if A cites B, then B is_cited_by A)
   - Implemented via database triggers or application logic

3. **Path Discovery**
   - Find chains of influence between distant texts
   - Example: "Show the intellectual pathway from Kant to Derrida on the concept of 'truth'"

4. **Conceptual Inheritance**
   - If text A defines a concept and text B extends A, infer B inherits that concept
   - Useful for building concept genealogies

5. **Contextual Clustering**
   - Infer relationships between texts that share multiple connections to the same texts
   - "These texts likely belong together because they cite similar sources"

Again not an exhaustive list and it should be relatively easy to extend the capabilities of this system with regards to inference. But also since all text elements will have a semantic embedding component, we hopefully will be able to have the following (non-exhaustive) capabilities:

## Enhanced Inference Capabilities

1. **Semantic Relationship Validation**
   - Verify explicit relationships by measuring semantic similarity
   - Example: If text A supposedly "extends" text B, their embeddings should have meaningful similarity

2. **Relationship Discovery**
   - Suggest potential relationships between semantically similar texts that lack explicit connections
   - "These texts have 90% semantic similarity but no recorded relationship - consider adding one"

3. **Conceptual Drift Analysis**
   - Track how concepts evolve through intellectual history by comparing embeddings along relationship chains
   - "How did 'truth' semantically shift from Kant to Hegel to Marx?"

4. **Weighted Path Discovery**
   - Enhance relationship paths by incorporating semantic relevance scores
   - "Show the path from Kant to Derrida, prioritizing texts with high semantic similarity to 'deconstruction'"

5. **Cross-School Concept Mapping**
   - Identify semantically similar discussions across different philosophical traditions
   - "Show Continental philosophy texts that discuss concepts semantically similar to Wittgenstein's 'language games'"


Another use case is writing an essay, if I am writing an essay in general, I may want to use a wider scope of my library, if I am writing an essay for a class, I may want to only search through specific texts. It should also have capabilities to assist me in the essay writing process, for example I might have a rough draft for a class and then ask if I have missed any sections of the assigned texts that may contradict with my interpretation, or on the other hand I can ask for supporting quotations. Or I can simply just ask for suggestions on reading material given a vague thesis I'd like to investigate further.

Or on the MCP side of things if I task an AI Agent with writing an essay or filling out my draft using examples, the AI Agent must be able to interface nicely with the MCP Server, this could also be a part of or a separate application. I'm unsure how we should divide up this project and modularize everything. Or I don't know enough about MCP Servers and vector databases (which I'm unsure which we should choose perhaps supabase? or have it be local since this will only be a tool for me but I might eventually want to craft up a plan to commercialize it, to help sell it).

We should have a good suite of varied user stories, for example essay writers, students, philosophy professors, self-educators, and look an explore other possibilities through a back and forth dialogue, with you guiding me through this process and trying to better assess my needs and the many different possible use cases while adhering to best design principles of usability, maintainability, scalability etc.

I'd like to also potentially turn this into a product to serve the philosophy community possibly a PWYC system. So part of this might involve, alongwith a CLI, an MCP interface, to have it hosted as a website. And perhaps community features that might be useful for organic growth. Whether or not we can also integrate it with a philosophy social network similar to the way GROK is integrated with X, where people can have their private libraries or share ideas / debate in an environment where references can easily be brought up, perhaps discoverability and sharing.

And so one of the decisions im wrestling with is whether to have it online, whether that will be feasable to host, at least in its primitive format, without a website, I don't want it to be flashy, I mean we won't be using any pictures, just storing text.

We'll also need a pipeline for processing texts into a suitable format for the database, and also perhaps a mini reader, whether again that be in the command line or we do a very simple browser interface (or both). But for now we will only accept text, epubs and markdown files.

We also need to think of our value proposition, what can we do differently to better serve this community than others? What are the issues what do people struggle with?

One of the useful features could be a bibliography manager, that could be in the form of a list manager, for example people can search through quotes / sections of text just as they might do tweets and add the chunks or their own independent selections (which might have to be constructed from the text chunks) to lists, and favourite them etc., and then operations can be done on that list like for example, "create the draft plan of an essay using these quotes". We'll have to be integrated with Gemini 2.5 Pro exp (recently released and is amazing but has rate limits), or just offer different models and versions like Cline or coding assistants do and have them input their own API keys. And so we'll also need some kind of simple reader as well, though this will be for the browser. This isn't for embedding but for the AI Agent that interfaces with the MCP Server.

A brainstorming possibility? Might we somehow be able to integrate with calibre since its open source? I'm unsure, we couldn't just create a plugin, we'd have to fork it and create our own version of calibre where this is a primary feature of it. 

## UPDATE: 04/02/2025 4:23AM

One thing I want to also include is the possibility of exploring Non-hierarchical relationships, I'm saying this because the project specifications say that everything will be organized hierarchically, that is the default way yes, that is normally how things are organized, but there are texts like 1000 Plateaus by Deleuze and Guattari that try to break free from that and I wonder if we could have this to also be a tool to help explore that space, through a suite of visualization tools, rearrangement tools, etc. like what if the text was organized differently? There are some philosophy texts for which that question is interesting.



## UPDATE: 04/02/2025 4:27AM
I want something, and I want the plan to reflect this, that offers immediate utility for the project of simply writing good essays and doing good research for a user that is coding capable (i.e. I wonder if we should just start it off as a basic MCP Server, that a chatbot like Claude can use to run searches and other things to help write essays), but is infinitely expandable to all the other things. And we need a cohesive pitch, and a quality exciting vision with a timeline of feature addition that if only funded such that I could work solely on things like this, I'd be able to produce. 

## UPDATE: 04/02/2025 4:27AM
system should also be able to handle transcripts of talks or lectures, I wonder as well if there is a quercus API that we could access to enable us to download and process readings.

## UPDATE: 04/03/2025 1:50AM
One of the cases we will have to deal with is not just having a robust reference management system, where works are explicitly cited, but also a robust note management system, where (and this is even if we don't have the text in the library) we process all the footnotes, where they are, which text_elements they refer to in the "referring text" (i.e. the one with the footnote). So to give an example, if there was a footnote with a reference in Part 1, Chapter 2, Section 6, Paragraph 6 of a certain book, that text_element would contain a relation entry connecting it to whatever was referenced.

We also need to figure out someway to automatically generate a bibliography or works cited as easy as possible. The issue is that there are different citation formats and different expectations, and if we ask for EPUBs, epubs typically don't have page numbers. Although some texts like hegel, or canonical philosophy texts with many different translations, will have paragraph and section numbers or their own unique way of citing which will typically be present in epubs. Yet page numbers, if we can somehow get access, would be the safest option. Like for example, if the PDF version of a book or essay or whatever is also available, same translation and everything, we could try to locate the text chunk in the PDF and then also locate the page number as well that on the same page. 

We need a good pipeline for inputting documents, if there is missing metadata prompt for it, it also must be error resilient (is the meta data we've scraped correct?). We will start with a CLI for this but extend it later to a UI. It also needs to be efficient, we need to give the option not to input docs one at a time, allow to input enter folders. We should also organize and sort source text documents in a folder system locally (this is in addition to the vectordatabase), so that the user can quickly open up the source document (preferably some way of opening it such that it is opened at the desired text_element location if that is requested).

Basically, think of all the ways we can make not just essay writing but all possible use cases of this easier, although we will focus on implementing making high quality and original philosophy essay writing easiest first and then expand to other possible applications.