import type { SupabaseClient } from '@supabase/supabase-js'
import type { ILogger } from '../../../lib/utils/logging'
import type { IRepository } from '../../shared/persistence/IRepository'
import { logSupabaseFailure } from './supabaseErrors'

/**
 * Configuration for {@link SupabaseCrudRepository}.
 */
export type SupabaseCrudRepositoryOptions = {
  /** Supabase table name (e.g. `extraction`). */
  table: string
  /** Primary key column name. Defaults to `id`. */
  idColumn?: string
  /** Select clause. Defaults to `*`. */
  select?: string
  /** Conflict target for upserts (Supabase `onConflict`). Defaults to `idColumn`. */
  upsertOnConflict?: string
}

/**
 * Base class for standard Supabase table-backed CRUD repositories.
 *
 * Design goals:
 * - Provide a consistent, typed implementation for the generic {@link IRepository} contract.
 * - Centralize Supabase error logging via {@link logSupabaseFailure}.
 * - Keep domain repositories focused on domain-specific queries.
 *
 * Non-goals:
 * - This class is *not* used for auth (`supabase.auth.*`) or storage.
 * - It does not implement domain-specific list filters/sorts.
 */
export abstract class SupabaseCrudRepository<TEntity, TCreate, TUpdate> implements IRepository<
  TEntity,
  TCreate,
  TUpdate
> {
  protected readonly supabase: SupabaseClient
  protected readonly logger: ILogger

  protected readonly table: string
  protected readonly idColumn: string
  protected readonly select: string
  protected readonly upsertOnConflict: string

  protected constructor(supabase: SupabaseClient, logger: ILogger, options: SupabaseCrudRepositoryOptions) {
    this.supabase = supabase
    this.logger = logger

    this.table = options.table
    this.idColumn = options.idColumn ?? 'id'
    this.select = options.select ?? '*'
    this.upsertOnConflict = options.upsertOnConflict ?? this.idColumn
  }

  async findById(id: string): Promise<TEntity | null> {
    const { data, error } = await this.supabase.from(this.table).select(this.select).eq(this.idColumn, id).maybeSingle()

    if (error) {
      logSupabaseFailure(this.logger, this.constructor.name, 'findById failed', error)
      throw error
    }

    return (data as TEntity | null) ?? null
  }

  async findAll(): Promise<TEntity[]> {
    const { data, error } = await this.supabase.from(this.table).select(this.select)

    if (error) {
      logSupabaseFailure(this.logger, this.constructor.name, 'findAll failed', error)
      throw error
    }

    return (data as TEntity[]) ?? []
  }

  async create(input: TCreate): Promise<TEntity> {
    const { data, error } = await this.supabase.from(this.table).insert(input).select(this.select).single()

    if (error) {
      logSupabaseFailure(this.logger, this.constructor.name, 'create failed', error)
      throw error
    }

    return data as TEntity
  }

  async upsert(input: TCreate): Promise<TEntity> {
    const { data, error } = await this.supabase
      .from(this.table)
      .upsert(input, { onConflict: this.upsertOnConflict })
      .select(this.select)
      .single()

    if (error) {
      logSupabaseFailure(this.logger, this.constructor.name, 'upsert failed', error)
      throw error
    }

    return data as TEntity
  }

  async update(id: string, patch: TUpdate): Promise<TEntity> {
    const { data, error } = await this.supabase
      .from(this.table)
      .update(patch)
      .eq(this.idColumn, id)
      .select(this.select)
      .single()

    if (error) {
      logSupabaseFailure(this.logger, this.constructor.name, 'update failed', error)
      throw error
    }

    return data as TEntity
  }

  async delete(id: string): Promise<void> {
    const { error } = await this.supabase.from(this.table).delete().eq(this.idColumn, id)

    if (error) {
      logSupabaseFailure(this.logger, this.constructor.name, 'delete failed', error)
      throw error
    }
  }
}
