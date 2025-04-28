# PhiloGraph Tier 0 - Pseudocode: Database Interaction Layer

## Overview

This module provides functions for interacting with the PostgreSQL database, which includes the `pgvector` extension. It abstracts the SQL queries needed for CRUD operations, vector search, and basic relationship management.

**Assumed Schema Concepts:**

*   `documents`: (id, title, author, year, source_path, metadata_jsonb)
*   `sections`: (id, doc_id, title, level, sequence)
*   `chunks`: (id, section_id, text_content, sequence, embedding vector(`{{TARGET_EMBEDDING_DIMENSION}}`))
*   `references`: (id, source_chunk_id, cited_doc_details_jsonb)
*   `relationships`: (id, source_node_id, target_node_id, relation_type, metadata_jsonb)
*   `collections`: (id, name)
*   `collection_items`: (collection_id, item_type, item_id)

**Configuration:**

*   Database connection details (host, port, user, password, dbname) obtained via environment variables (`{{DB_HOST}}`, `{{DB_PORT}}`, etc.).

```pseudocode
// --- Configuration ---
CONSTANT DB_CONFIG = load_db_config_from_env()
CONSTANT TARGET_DIMENSION = {{TARGET_EMBEDDING_DIMENSION}} // e.g., 768 or 1024

// --- Connection Management ---
FUNCTION get_db_connection():
    // TDD: Test connection successful with valid config
    // TDD: Test connection failure with invalid config
    TRY:
        connection = connect_to_postgres(DB_CONFIG)
        RETURN connection
    CATCH DatabaseError as e:
        log_error("Failed to connect to database", e)
        RAISE ConnectionError("Database connection failed")
END FUNCTION

FUNCTION close_db_connection(connection):
    // TDD: Test connection closes properly
    IF connection IS NOT NULL:
        connection.close()
END FUNCTION

// --- Document Operations ---
FUNCTION add_document(connection, title, author, year, source_path, metadata):
    // TDD: Test adding a new document returns a valid ID
    // TDD: Test adding a document with existing source_path (handle appropriately - update or error?)
    // TDD: Test handling of null/empty values for optional fields
    sql = "INSERT INTO documents (title, author, year, source_path, metadata_jsonb) VALUES (%s, %s, %s, %s, %s) RETURNING id;"
    params = (title, author, year, source_path, json_serialize(metadata))
    cursor = connection.cursor()
    cursor.execute(sql, params)
    document_id = cursor.fetchone()[0]
    connection.commit()
    cursor.close()
    RETURN document_id
END FUNCTION

FUNCTION get_document_by_id(connection, doc_id):
    // TDD: Test retrieving an existing document
    // TDD: Test retrieving a non-existent document returns None
    sql = "SELECT id, title, author, year, source_path, metadata_jsonb FROM documents WHERE id = %s;"
    cursor = connection.cursor()
    cursor.execute(sql, (doc_id,))
    result = cursor.fetchone()
    cursor.close()
    IF result:
        RETURN map_row_to_document_object(result)
    ELSE:
        RETURN NULL
END FUNCTION

FUNCTION check_document_exists(connection, source_path):
    // TDD: Test returns True for existing document by source_path
    // TDD: Test returns False for non-existent document by source_path
    sql = "SELECT EXISTS(SELECT 1 FROM documents WHERE source_path = %s);"
    cursor = connection.cursor()
    cursor.execute(sql, (source_path,))
    exists = cursor.fetchone()[0]
    cursor.close()
    RETURN exists
END FUNCTION

// --- Section Operations ---
FUNCTION add_section(connection, doc_id, title, level, sequence):
    // TDD: Test adding a section returns a valid ID
    // TDD: Test adding section linked to non-existent doc_id raises error
    sql = "INSERT INTO sections (doc_id, title, level, sequence) VALUES (%s, %s, %s, %s) RETURNING id;"
    params = (doc_id, title, level, sequence)
    cursor = connection.cursor()
    cursor.execute(sql, params)
    section_id = cursor.fetchone()[0]
    connection.commit()
    cursor.close()
    RETURN section_id
END FUNCTION

// --- Chunk Operations ---
FUNCTION add_chunk(connection, section_id, text_content, sequence, embedding_vector):
    // TDD: Test adding a chunk returns a valid ID
    // TDD: Test adding chunk with embedding of incorrect dimension raises error
    // TDD: Test adding chunk linked to non-existent section_id raises error
    ASSERT length(embedding_vector) == TARGET_DIMENSION

    sql = "INSERT INTO chunks (section_id, text_content, sequence, embedding) VALUES (%s, %s, %s, %s) RETURNING id;"
    // Ensure embedding_vector is formatted correctly for pgvector (e.g., '[1.0, 2.0, ...]')
    formatted_embedding = format_vector_for_pgvector(embedding_vector)
    params = (section_id, text_content, sequence, formatted_embedding)
    cursor = connection.cursor()
    cursor.execute(sql, params)
    chunk_id = cursor.fetchone()[0]
    connection.commit()
    cursor.close()
    RETURN chunk_id
END FUNCTION

FUNCTION add_chunks_batch(connection, chunks_data):
    // chunks_data: list of tuples (section_id, text_content, sequence, embedding_vector)
    // TDD: Test adding multiple chunks successfully
    // TDD: Test rollback on error during batch insert
    // TDD: Test performance compared to single inserts
    // Consider using psycopg2's execute_values for efficiency
    sql = "INSERT INTO chunks (section_id, text_content, sequence, embedding) VALUES %s;"
    formatted_data = []
    FOR section_id, text_content, sequence, embedding_vector in chunks_data:
        ASSERT length(embedding_vector) == TARGET_DIMENSION
        formatted_embedding = format_vector_for_pgvector(embedding_vector)
        formatted_data.append((section_id, text_content, sequence, formatted_embedding))

    cursor = connection.cursor()
    // Use execute_values or similar batch execution method
    execute_batch(cursor, sql, formatted_data)
    connection.commit()
    cursor.close()
END FUNCTION

// --- Reference Operations ---
FUNCTION add_reference(connection, source_chunk_id, cited_doc_details):
    // TDD: Test adding a reference returns a valid ID
    // TDD: Test adding reference linked to non-existent chunk_id raises error
    sql = "INSERT INTO references (source_chunk_id, cited_doc_details_jsonb) VALUES (%s, %s) RETURNING id;"
    params = (source_chunk_id, json_serialize(cited_doc_details))
    cursor = connection.cursor()
    cursor.execute(sql, params)
    reference_id = cursor.fetchone()[0]
    connection.commit()
    cursor.close()
    RETURN reference_id
END FUNCTION

// --- Search Operations ---
FUNCTION vector_search_chunks(connection, query_embedding, top_k, filters = NULL):
    // TDD: Test basic vector search returns correct number of results (top_k)
    // TDD: Test vector search with metadata filters (e.g., author, year)
    // TDD: Test search with empty query_embedding raises error
    // TDD: Test search with embedding of incorrect dimension raises error
    // TDD: Test different distance metrics (L2, cosine) if needed
    ASSERT length(query_embedding) == TARGET_DIMENSION

    // Base query - adjust distance metric (<=> L2, <-> Cosine) as needed
    base_sql = """
        SELECT c.id, c.text_content, c.sequence, s.id as section_id, s.title as section_title,
               d.id as doc_id, d.title as doc_title, d.author as doc_author, d.year as doc_year, d.source_path,
               c.embedding <=> %s AS distance
        FROM chunks c
        JOIN sections s ON c.section_id = s.id
        JOIN documents d ON s.doc_id = d.id
    """
    where_clauses = []
    params = [format_vector_for_pgvector(query_embedding)]

    IF filters IS NOT NULL:
        // TDD: Test filter construction for various valid filter types
        // TDD: Test filter construction handles invalid/malformed filters gracefully
        IF 'author' in filters:
            where_clauses.append("d.author = %s")
            params.append(filters['author'])
        IF 'year' in filters:
            where_clauses.append("d.year = %s")
            params.append(filters['year'])
        IF 'doc_id' in filters:
            where_clauses.append("d.id = %s")
            params.append(filters['doc_id'])
        // Add more filters as needed (e.g., tags in metadata_jsonb)

    sql = base_sql
    IF where_clauses:
        sql += " WHERE " + " AND ".join(where_clauses)

    sql += " ORDER BY distance ASC LIMIT %s;"
    params.append(top_k)

    cursor = connection.cursor()
    cursor.execute(sql, tuple(params))
    results = cursor.fetchall()
    cursor.close()

    // TDD: Test mapping of results to structured objects
    RETURN map_rows_to_search_result_objects(results)
END FUNCTION

// --- Relationship Operations (Basic) ---
FUNCTION add_relationship(connection, source_node_id, target_node_id, relation_type, metadata = NULL):
    // TDD: Test adding a 'cites' relationship
    // TDD: Test adding relationship with non-existent nodes raises error
    sql = "INSERT INTO relationships (source_node_id, target_node_id, relation_type, metadata_jsonb) VALUES (%s, %s, %s, %s) RETURNING id;"
    params = (source_node_id, target_node_id, relation_type, json_serialize(metadata))
    cursor = connection.cursor()
    cursor.execute(sql, params)
    relationship_id = cursor.fetchone()[0]
    connection.commit()
    cursor.close()
    RETURN relationship_id
END FUNCTION

FUNCTION get_relationships(connection, node_id, direction = 'outgoing', relation_type = NULL):
    // direction: 'outgoing', 'incoming', 'both'
    // TDD: Test getting outgoing 'cites' relationships
    // TDD: Test getting incoming 'cites' relationships
    // TDD: Test getting relationships of a specific type
    // TDD: Test getting relationships for a non-existent node_id returns empty list
    base_sql = "SELECT id, source_node_id, target_node_id, relation_type, metadata_jsonb FROM relationships"
    where_clauses = []
    params = []

    IF direction == 'outgoing':
        where_clauses.append("source_node_id = %s")
        params.append(node_id)
    ELSE IF direction == 'incoming':
        where_clauses.append("target_node_id = %s")
        params.append(node_id)
    ELSE IF direction == 'both':
        where_clauses.append("(source_node_id = %s OR target_node_id = %s)")
        params.append(node_id)
        params.append(node_id)
    ELSE:
        RAISE ValueError("Invalid direction specified")

    IF relation_type IS NOT NULL:
        where_clauses.append("relation_type = %s")
        params.append(relation_type)

    sql = base_sql
    IF where_clauses:
        sql += " WHERE " + " AND ".join(where_clauses)

    cursor = connection.cursor()
    cursor.execute(sql, tuple(params))
    results = cursor.fetchall()
    cursor.close()
    RETURN map_rows_to_relationship_objects(results)
END FUNCTION

// --- Collection Operations ---
FUNCTION add_collection(connection, name):
    // TDD: Test adding a new collection
    sql = "INSERT INTO collections (name) VALUES (%s) RETURNING id;"
    cursor = connection.cursor()
    cursor.execute(sql, (name,))
    collection_id = cursor.fetchone()[0]
    connection.commit()
    cursor.close()
    RETURN collection_id
END FUNCTION

FUNCTION add_item_to_collection(connection, collection_id, item_type, item_id):
    // item_type: 'document', 'chunk', etc.
    // TDD: Test adding a document to a collection
    // TDD: Test adding a chunk to a collection
    // TDD: Test adding item to non-existent collection raises error
    sql = "INSERT INTO collection_items (collection_id, item_type, item_id) VALUES (%s, %s, %s);"
    params = (collection_id, item_type, item_id)
    cursor = connection.cursor()
    cursor.execute(sql, params)
    connection.commit()
    cursor.close()
END FUNCTION

FUNCTION get_collection_items(connection, collection_id):
    // TDD: Test retrieving items from a collection
    sql = "SELECT item_type, item_id FROM collection_items WHERE collection_id = %s;"
    cursor = connection.cursor()
    cursor.execute(sql, (collection_id,))
    results = cursor.fetchall()
    cursor.close()
    RETURN results // List of (item_type, item_id) tuples
END FUNCTION

// --- Utility Functions ---
FUNCTION format_vector_for_pgvector(vector):
    // TDD: Test formatting of list/numpy array to string '[1.0, 2.0,...]'
    RETURN '[' + ','.join(map(str, vector)) + ']'
END FUNCTION

FUNCTION json_serialize(data):
    // TDD: Test serialization of dict to JSON string
    // TDD: Test handling of None input
    IF data IS NULL:
        RETURN NULL
    RETURN json.dumps(data)
END FUNCTION

FUNCTION map_row_to_document_object(row):
    // TDD: Test mapping DB row to a Document data structure/object
    // ... implementation details ...
    RETURN document_object
END FUNCTION

FUNCTION map_rows_to_search_result_objects(rows):
    // TDD: Test mapping multiple DB rows to SearchResult objects
    // ... implementation details ...
    RETURN list_of_search_result_objects
END FUNCTION

FUNCTION map_rows_to_relationship_objects(rows):
    // TDD: Test mapping multiple DB rows to Relationship objects
    // ... implementation details ...
    RETURN list_of_relationship_objects
END FUNCTION