/** The real API client (no mocking of it): token header + automatic logout on an expired session. */
import { AxiosError } from "axios";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { api, getReport, login } from "../services/api";
import { useAuthStore } from "../store/authStore";
 
const original = api.defaults.adapter;
const respond = (status, data = {}) => (config) =>
  status < 400
    ? Promise.resolve({ data, status, statusText: "", headers: {}, config })
    : Promise.reject(new AxiosError("fail", "ERR_BAD_REQUEST", config, null, { status, data, statusText: "", headers: {}, config }));
 
beforeEach(() => useAuthStore.setState({ token: "tok", user: { name: "A" } }));
afterEach(() => { api.defaults.adapter = original; });
 
describe("api client", () => {
  it("sends the login token with every request", async () => {
    let seen;
    api.defaults.adapter = async (config) => { seen = config.headers.Authorization; return respond(200)(config); };
    await getReport("x");
    expect(seen).toBe("Bearer tok");
  });
 
  it("sends no Authorization header when logged out", async () => {
    useAuthStore.setState({ token: null, user: null });
    let seen = "unset";
    api.defaults.adapter = async (config) => { seen = config.headers.Authorization; return respond(200)(config); };
    await getReport("x");
    expect(seen).toBeUndefined();
  });
 
  it("a 401 on a normal request means the session expired: log out", async () => {
    api.defaults.adapter = async (config) => respond(401, { detail: "Not authenticated" })(config);
    await expect(getReport("x")).rejects.toBeTruthy();
    expect(useAuthStore.getState().token).toBeNull();
  });
 
  it("a 401 from login just means wrong credentials: it must not touch the session logic", async () => {
    api.defaults.adapter = async (config) => respond(401, { detail: "Invalid email or password" })(config);
    await expect(login({ email: "a@b.co", password: "x" })).rejects.toMatchObject({ response: { status: 401 } });
    expect(useAuthStore.getState().token).toBe("tok");
  });
 
  it("other failures (500, 404) never log the user out", async () => {
    for (const status of [404, 429, 500]) {
      api.defaults.adapter = async (config) => respond(status)(config);
      await expect(getReport("x")).rejects.toBeTruthy();
      expect(useAuthStore.getState().token).toBe("tok");
    }
  });
});
 












