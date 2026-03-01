/**
 * Generic repository contract used by the Studio service layer.
 *
 * Why this exists:
 * - Keeps domain services independent from concrete persistence (Supabase, HTTP, etc.).
 * - Makes it explicit which operations are supported for a given aggregate.
 *
 * Why we model multiple types (TEntity, TCreate, TUpdate):
 * - `TEntity` represents the shape returned from persistence (usually a DB row).
 * - `TCreate` represents the input required/allowed for creation (often excludes DB defaults).
 * - `TUpdate` represents the patch shape for updates (often partial; may be different from create).
 *
 * This separation prevents two common problems:
 * - "Everything optional" types that silently allow invalid writes.
 * - "Everything required" types that force clients to provide DB-generated/default fields.
 */
export interface IRepository<TEntity, TCreate, TUpdate> {
  /**
   * Find an entity by its primary identifier.
   */
  findById(id: string): Promise<TEntity | null>

  /**
   * List all entities.
   *
   * Note: many domains will expose domain-specific list methods instead (e.g. `findActive()`),
   * but the generic method is still useful for admin/debug flows.
   */
  findAll(): Promise<TEntity[]>

  /**
   * Create a new entity.
   */
  create(input: TCreate): Promise<TEntity>

  /**
   * Insert-or-update using the persistence layer's native upsert support.
   *
   * Typical semantics:
   * - If a row with the same primary key (or conflict key) exists, update it.
   * - Otherwise, insert a new row.
   */
  upsert(input: TCreate): Promise<TEntity>

  /**
   * Update an existing entity by id using a patch.
   */
  update(id: string, patch: TUpdate): Promise<TEntity>

  /**
   * Delete an existing entity by id.
   */
  delete(id: string): Promise<void>
}
