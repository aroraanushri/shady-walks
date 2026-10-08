import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { App } from "./main";

const analysis = {
  filename: "street.jpg",
  gvi_percent: 22.14,
  vegetation_pixels: 174096,
  valid_pixels: 786432,
  vegetation_labels: ["tree"],
  device: "cpu",
  overlay_png_base64: "aGVsbG8=",
  limitation: "Observed vegetation only.",
};

describe("ShadeShift upload workflow", () => {
  it("shows loading and genuine analysis results", async () => {
    let resolveRequest: (value: Response) => void = () => undefined;
    vi.stubGlobal("fetch", vi.fn(() => new Promise((resolve) => {
      resolveRequest = resolve;
    })));
    render(<App />);
    const input = screen.getByTestId("upload-control").querySelector("input")!;
    fireEvent.change(input, {
      target: { files: [new File(["pixels"], "street.jpg", { type: "image/jpeg" })] },
    });
    expect(await screen.findByRole("status")).toHaveTextContent("Analyzing image");
    resolveRequest(new Response(JSON.stringify(analysis), { status: 200 }));
    expect(await screen.findByTestId("gvi-result")).toHaveTextContent("22.14%");
  });

  it("displays API errors", async () => {
    vi.stubGlobal("fetch", vi.fn(() => Promise.resolve(
      new Response(JSON.stringify({ detail: "Mapillary analysis failed." }), { status: 502 }),
    )));
    render(<App />);
    const input = screen.getByTestId("upload-control").querySelector("input")!;
    fireEvent.change(input, {
      target: { files: [new File(["pixels"], "street.jpg", { type: "image/jpeg" })] },
    });
    await waitFor(() => expect(screen.getByRole("alert")).toHaveTextContent("Mapillary analysis failed."));
  });

  it("selects a Mapillary marker and displays its analysis", async () => {
    const image = {
      id: "123456789",
      longitude: 73.8567,
      latitude: 18.5204,
      captured_at: Date.now(),
      thumb_1024_url: "https://scontent.example.fbcdn.net/image.jpg",
      attribution: "Mapillary / tester",
    };
    vi.stubGlobal("fetch", vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ images: [image], count: 1 }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify(analysis), { status: 200 })));
    render(<App />);

    fireEvent.click(await screen.findByRole("button", { name: "Marker" }));
    fireEvent.click(await screen.findByRole("button", { name: "Analyze this image" }));

    expect(await screen.findByTestId("gvi-result")).toHaveTextContent("22.14%");
  });

  it("shows Mapillary loading failures", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ detail: "Imagery unavailable." }), { status: 503 }),
    ));
    render(<App />);

    await waitFor(() => expect(screen.getByText("Imagery unavailable.")).toBeInTheDocument());
  });
});
