# Synthetic paraphrase authored for this corpus

This corpus explains how a compact caching layer decides when to evict entries
from memory. The layer tracks each entry's recent access time and its estimated
rebuild cost, then ranks candidates by a weighted combination of the two.
Entries that are cheap to rebuild and rarely accessed are evicted first, while
expensive, frequently used entries are retained as long as possible. A
background sweep runs every several minutes so eviction decisions never block
a request in progress.
