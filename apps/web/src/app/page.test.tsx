import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import HomePage from "./page";

describe("HomePage", () => {
  it("renders the product name as the main heading", () => {
    expect(renderToStaticMarkup(<HomePage />)).toContain(
      "<h1>Commerce OS</h1>",
    );
  });
});
