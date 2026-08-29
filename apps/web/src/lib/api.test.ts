import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";

import { describe, expect, it, vi } from "vitest";

import { getGame, searchGames } from "./api";

describe("public-api/v1 consumer", () => {
  it("consumes the checked-in representative detail fixture", async () => {
    const fixtureUrl = new URL(
      "../../../../contracts/public-api/v1/examples/sample-game.json",
      import.meta.url,
    );
    const fixture = JSON.parse(await readFile(fileURLToPath(fixtureUrl), "utf8"));
    const fetcher = vi.fn().mockResolvedValue(new Response(JSON.stringify(fixture), { status: 200 }));

    const result = await getGame(fixture.game.id, "http://backend", fetcher);

    expect(result.aggregates[0]?.median_minutes).toBe(720);
    expect(result.aggregates[0]?.revision_number).toBe(1);
  });

  it("retries one 503 then returns a valid search response", async () => {
    const fetcher = vi
      .fn()
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            contract: "public-api/v1",
            error: { code: "unavailable", correlation_id: crypto.randomUUID() },
          }),
          { status: 503 },
        ),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ contract: "public-api/v1", results: [] }), { status: 200 }),
      );

    await expect(searchGames("샘플", "http://backend", fetcher)).resolves.toEqual({
      contract: "public-api/v1",
      results: [],
    });
    expect(fetcher).toHaveBeenCalledTimes(2);
  });

  it("does not retry a 400 response", async () => {
    const fetcher = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          contract: "public-api/v1",
          error: { code: "invalid_search_query", correlation_id: "correlation" },
        }),
        { status: 400 },
      ),
    );

    await expect(searchGames("", "http://backend", fetcher)).rejects.toMatchObject({
      code: "invalid_search_query",
      status: 400,
    });
    expect(fetcher).toHaveBeenCalledTimes(1);
  });

  it("rejects an incompatible success body", async () => {
    const fetcher = vi.fn().mockResolvedValue(new Response(JSON.stringify({ results: [] })));

    await expect(searchGames("샘플", "http://backend", fetcher)).rejects.toMatchObject({
      code: "invalid_backend_contract",
    });
  });
});
