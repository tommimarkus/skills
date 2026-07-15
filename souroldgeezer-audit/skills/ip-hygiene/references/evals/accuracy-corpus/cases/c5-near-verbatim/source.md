# Synthetic source authored for this corpus

This corpus explains how a small caching layer decides when to evict entries
from memory. The layer tracks each entry's last access time and its estimated
rebuild cost, then ranks candidates by a weighted combination of the two.
Entries that are cheap to rebuild and rarely accessed are evicted first, while
expensive, frequently used entries are kept as long as possible. A background
sweep runs every few minutes so eviction decisions never block a request in
progress.
