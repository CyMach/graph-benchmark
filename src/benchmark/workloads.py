from dataclasses import dataclass


@dataclass(frozen=True)
class Workload:
    name: str
    query: str
    parameter_kind: str


WORKLOADS = [
    Workload(
        name="1_hop_habitat",
        query="""
        MATCH (m:Mushroom {id: $id})
              -[:IN_HABITAT]->
              (h:Habitat)
        RETURN h.value AS value
        """,
        parameter_kind="mushroom_id",
    ),

    Workload(
        name="2_hop_shared_stem_root",
        query="""
        MATCH (m:Mushroom {id: $id})
              -[:HAS_STEM_ROOT]->
              (r:StemRoot)
              <-[:HAS_STEM_ROOT]-
              (other:Mushroom)
        WHERE other.id <> m.id
        RETURN other.id AS id
        """,
        parameter_kind="mushroom_id",
    ),

    Workload(
        name="3_hop_stem_root_season",
        query="""
        MATCH (m:Mushroom {id: $id})
              -[:HAS_STEM_ROOT]->
              (r:StemRoot)
              <-[:HAS_STEM_ROOT]-
              (other:Mushroom)
              -[:IN_SEASON]->
              (s:Season)
        WHERE other.id <> m.id
        RETURN other.id AS id,
               s.value AS season
        """,
        parameter_kind="mushroom_id",
    ),

    Workload(
        name="point_lookup",
        query="""
        MATCH (m:Mushroom {id: $id})
        RETURN m.id AS id,
               m.class AS class,
               m.cap_diameter AS cap_diameter,
               m.stem_height AS stem_height,
               m.stem_width AS stem_width
        """,
        parameter_kind="mushroom_id",
    ),

    Workload(
        name="indexed_habitat_lookup",
        query="""
        MATCH (h:Habitat {value: $value})
        MATCH (m:Mushroom)-[:IN_HABITAT]->(h)
        RETURN count(m) AS count
        """,
        parameter_kind="habitat",
    ),

    Workload(
        name="aggregation",
        query="""
        MATCH (m:Mushroom)
        RETURN m.class AS class,
               count(*) AS count
        ORDER BY class
        """,
        parameter_kind="none",
    ),

    Workload(
        name="mixed_read_write_sequential_baseline",
        query="""
        MATCH (m:Mushroom {id: $id})
        SET m.benchmark_touch = $value
        RETURN m.id AS id,
               m.benchmark_touch AS value
        """,
        parameter_kind="mushroom_id_write",
    ),
]
