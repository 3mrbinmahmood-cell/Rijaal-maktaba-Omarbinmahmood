-- Rijaal Maktaba Omar bin Mahmood — production data model v0.1
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS narrators (
  narrator_id TEXT PRIMARY KEY,
  canonical_name TEXT NOT NULL,
  short_name TEXT,
  shamela_id INTEGER UNIQUE,
  identity_status TEXT NOT NULL CHECK(identity_status IN ('resolved','provisional','ambiguous','unresolved')),
  summary_grade TEXT,
  summary_grade_source TEXT,
  created_from TEXT NOT NULL,
  review_status TEXT NOT NULL DEFAULT 'unreviewed'
);

CREATE TABLE IF NOT EXISTS narrator_aliases (
  alias_id TEXT PRIMARY KEY,
  narrator_id TEXT NOT NULL REFERENCES narrators(narrator_id),
  alias_text TEXT NOT NULL,
  normalized_alias TEXT NOT NULL,
  alias_type TEXT NOT NULL,
  source_reference_id TEXT,
  UNIQUE(narrator_id, normalized_alias, alias_type)
);
CREATE INDEX IF NOT EXISTS idx_alias_norm ON narrator_aliases(normalized_alias);

CREATE TABLE IF NOT EXISTS narrator_biography_evidence (
  evidence_id TEXT PRIMARY KEY,
  narrator_id TEXT NOT NULL REFERENCES narrators(narrator_id),
  source_title TEXT NOT NULL,
  source_locator TEXT,
  exact_text TEXT NOT NULL,
  evidence_type TEXT NOT NULL,
  source_url TEXT,
  source_reference_id TEXT
);

CREATE TABLE IF NOT EXISTS narrator_judgments (
  judgment_id TEXT PRIMARY KEY,
  narrator_id TEXT NOT NULL REFERENCES narrators(narrator_id),
  critic_name TEXT NOT NULL,
  exact_judgment TEXT NOT NULL,
  normalized_grade TEXT,
  source_title TEXT NOT NULL,
  source_locator TEXT,
  source_reference_id TEXT,
  is_summary_source INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_judgment_narrator ON narrator_judgments(narrator_id);

CREATE TABLE IF NOT EXISTS narrator_events (
  event_id TEXT PRIMARY KEY,
  narrator_id TEXT NOT NULL REFERENCES narrators(narrator_id),
  event_type TEXT NOT NULL,
  year_from_hijri INTEGER,
  year_to_hijri INTEGER,
  date_precision TEXT,
  place_name TEXT,
  exact_text TEXT,
  source_title TEXT NOT NULL,
  source_locator TEXT,
  source_reference_id TEXT
);
CREATE INDEX IF NOT EXISTS idx_event_narrator_type ON narrator_events(narrator_id,event_type);

CREATE TABLE IF NOT EXISTS narrator_traits (
  trait_id TEXT PRIMARY KEY,
  narrator_id TEXT NOT NULL REFERENCES narrators(narrator_id),
  trait_type TEXT NOT NULL,
  trait_value TEXT NOT NULL,
  year_from_hijri INTEGER,
  year_to_hijri INTEGER,
  exact_text TEXT,
  source_title TEXT NOT NULL,
  source_locator TEXT,
  source_reference_id TEXT
);

-- Direction is always STUDENT -> TEACHER.
CREATE TABLE IF NOT EXISTS narrator_relationships (
  relationship_id TEXT PRIMARY KEY,
  student_id TEXT NOT NULL REFERENCES narrators(narrator_id),
  teacher_id TEXT NOT NULL REFERENCES narrators(narrator_id),
  relationship_status TEXT NOT NULL,
  UNIQUE(student_id,teacher_id)
);
CREATE INDEX IF NOT EXISTS idx_rel_student ON narrator_relationships(student_id);
CREATE INDEX IF NOT EXISTS idx_rel_teacher ON narrator_relationships(teacher_id);

CREATE TABLE IF NOT EXISTS relationship_evidence (
  evidence_id TEXT PRIMARY KEY,
  relationship_id TEXT NOT NULL REFERENCES narrator_relationships(relationship_id),
  evidence_kind TEXT NOT NULL,
  transmission_term TEXT,
  sanad_id TEXT,
  hadith_record_id TEXT,
  source_title TEXT NOT NULL,
  source_locator TEXT,
  exact_text TEXT,
  source_reference_id TEXT,
  evidence_strength TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_rel_evidence ON relationship_evidence(relationship_id,evidence_kind);

CREATE TABLE IF NOT EXISTS sanad_branches (
  branch_id TEXT PRIMARY KEY,
  sanad_id TEXT NOT NULL,
  branch_number INTEGER NOT NULL,
  source_file_id TEXT NOT NULL,
  hadith_record_id TEXT,
  original_sanad TEXT NOT NULL,
  evidence_layer TEXT NOT NULL,
  UNIQUE(sanad_id,branch_number)
);

CREATE TABLE IF NOT EXISTS sanad_nodes (
  node_id TEXT PRIMARY KEY,
  branch_id TEXT NOT NULL REFERENCES sanad_branches(branch_id),
  position INTEGER NOT NULL,
  raw_occurrence_id TEXT,
  raw_name TEXT NOT NULL,
  narrator_id TEXT REFERENCES narrators(narrator_id),
  resolution_status TEXT NOT NULL,
  resolution_method TEXT,
  resolution_confidence REAL,
  UNIQUE(branch_id,position)
);

CREATE TABLE IF NOT EXISTS sanad_edges (
  sanad_edge_id TEXT PRIMARY KEY,
  branch_id TEXT NOT NULL REFERENCES sanad_branches(branch_id),
  from_node_id TEXT NOT NULL REFERENCES sanad_nodes(node_id),
  to_node_id TEXT NOT NULL REFERENCES sanad_nodes(node_id),
  transmission_term TEXT,
  original_link_text TEXT,
  UNIQUE(branch_id,from_node_id,to_node_id)
);

-- Derived evidence-based analyzer output. Safe to rebuild at any time.
CREATE TABLE IF NOT EXISTS sanad_edge_analysis (
  sanad_edge_id TEXT PRIMARY KEY REFERENCES sanad_edges(sanad_edge_id),
  analyzer_version TEXT NOT NULL,
  identity_resolved INTEGER NOT NULL,
  chronology_status TEXT,
  reported_teacher_student_status TEXT,
  observed_corpus_status TEXT,
  explicit_samaa_status TEXT,
  meeting_status TEXT,
  geography_status TEXT,
  tadlis_status TEXT,
  continuity_status TEXT,
  weakness_status TEXT,
  overall_link_status TEXT,
  explanation_json TEXT NOT NULL,
  computed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sanad_narrator_analysis (
  node_id TEXT PRIMARY KEY REFERENCES sanad_nodes(node_id),
  analyzer_version TEXT NOT NULL,
  narrator_grade_status TEXT,
  ikhtilat_status TEXT,
  tadlis_status TEXT,
  identity_warning TEXT,
  explanation_json TEXT NOT NULL,
  computed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sanad_analysis_summary (
  branch_id TEXT PRIMARY KEY REFERENCES sanad_branches(branch_id),
  analyzer_version TEXT NOT NULL,
  continuity_summary TEXT,
  weak_narrator_count INTEGER NOT NULL DEFAULT 0,
  broken_link_count INTEGER NOT NULL DEFAULT 0,
  uncertain_link_count INTEGER NOT NULL DEFAULT 0,
  automated_assessment TEXT,
  existing_scholar_gradings_json TEXT,
  computed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
