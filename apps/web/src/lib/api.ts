export type GameSummary = {
  id: string;
  slug: string;
  korean_title: string;
  original_title: string;
};

export type PublicAggregate = {
  platform: { id: string; code: string; label: string };
  completion_scope: "main_story" | "main_plus_optional" | "completionist";
  status: "insufficient_data" | "published";
  median_minutes?: number;
  sample_count?: number;
  rule_revision?: "median-v1";
  revision_id?: string;
  revision_number?: number;
};

export type SearchResponse = { contract: "public-api/v1"; results: GameSummary[] };
export type DetailResponse = {
  contract: "public-api/v1";
  game: GameSummary;
  aggregates: PublicAggregate[];
};

export class PublicApiError extends Error {
  constructor(
    public code: string,
    public status: number,
    public correlationId: string,
  ) {
    super(code);
  }
}

type Fetcher = typeof fetch;

async function request(path: string, apiBase: string, fetcher: Fetcher): Promise<unknown> {
  let lastError: unknown;
  for (let attempt = 0; attempt < 2; attempt += 1) {
    try {
      const response = await fetcher(`${apiBase}${path}`, {
        headers: { accept: "application/json" },
        signal: AbortSignal.timeout(5000),
      });
      if (response.ok) return response.json();
      const body = (await response.json().catch(() => ({}))) as {
        error?: { code?: string; correlation_id?: string };
      };
      const correlationId = body.error?.correlation_id ?? crypto.randomUUID();
      const code = body.error?.code ?? "backend_unavailable";
      if ((response.status === 502 || response.status === 503) && attempt === 0) {
        lastError = new PublicApiError(code, response.status, correlationId);
        continue;
      }
      throw new PublicApiError(code, response.status, correlationId);
    } catch (error) {
      if (error instanceof PublicApiError && error.status < 500) throw error;
      lastError = error;
      if (attempt === 1) break;
    }
  }
  if (lastError instanceof PublicApiError) throw lastError;
  throw new PublicApiError("backend_unavailable", 503, crypto.randomUUID());
}

function assertContract(value: unknown): asserts value is Record<string, unknown> {
  if (!value || typeof value !== "object" || (value as { contract?: unknown }).contract !== "public-api/v1") {
    throw new PublicApiError("invalid_backend_contract", 503, crypto.randomUUID());
  }
}

export async function searchGames(
  query: string,
  apiBase: string,
  fetcher: Fetcher = fetch,
): Promise<SearchResponse> {
  const value = await request(`/api/v1/games?query=${encodeURIComponent(query)}`, apiBase, fetcher);
  assertContract(value);
  if (!Array.isArray(value.results)) {
    throw new PublicApiError("invalid_backend_contract", 503, crypto.randomUUID());
  }
  return value as SearchResponse;
}

export async function getGame(
  gameId: string,
  apiBase: string,
  fetcher: Fetcher = fetch,
): Promise<DetailResponse> {
  const value = await request(`/api/v1/games/${encodeURIComponent(gameId)}`, apiBase, fetcher);
  assertContract(value);
  if (!value.game || !Array.isArray(value.aggregates)) {
    throw new PublicApiError("invalid_backend_contract", 503, crypto.randomUUID());
  }
  return value as DetailResponse;
}
