"""Exercise input boundaries, provider contracts and HTTP access isolation."""
import copy
import io
import json
import sys
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))
from app import OnCueServer
from engine import AppError, MiniMaxProvider, SCENES, local_rehearsal, normalize_request, parse_model_result, route_warnings


def request_for(scene=0, trial=0, mode="demo"):
    s = SCENES[scene]
    return {"scene_name": s["name"], "messages": copy.deepcopy(s["messages"]),
            "trial": s["trials"][trial], "mode": mode, "consent": True}


class FakeResponse(io.BytesIO):
    pass


class FakeOpener:
    def __init__(self, content, status=200, finish="stop"):
        self.content, self.status, self.finish = content, status, finish
        self.request = None

    def open(self, req, timeout):
        self.request = req
        if self.status != 200:
            raise urllib.error.HTTPError(req.full_url, self.status, "test error", {}, None)
        value = {"choices": [{"message": {"content": self.content}, "finish_reason": self.finish}],
                 "usage": {"total_tokens": 123}, "base_resp": {"status_code": 0}}
        return FakeResponse(json.dumps(value).encode())


class EngineTests(unittest.TestCase):
    def test_scene_routes_have_real_evidence_and_fit_limits(self):
        for scene in range(3):
            for trial in range(3):
                payload = normalize_request(request_for(scene, trial))
                result = local_rehearsal(payload)
                self.assertEqual(result["mode"], "demo")
                self.assertEqual(len(result["routes"]), 3)
                parsed = parse_model_result(json.dumps(result), payload["messages"])
                self.assertEqual(len(parsed["routes"]), 3)

    def test_rewriting_travel_line_changes_route(self):
        first = local_rehearsal(normalize_request(request_for()))
        second = local_rehearsal(normalize_request(request_for(trial=1)))
        third = local_rehearsal(normalize_request(request_for(trial=2)))
        self.assertNotEqual(first["routes"][0]["draft"], second["routes"][0]["draft"])
        self.assertNotEqual(second["routes"][0]["draft"], third["routes"][0]["draft"])

    def test_custom_scene_does_not_inherit_travel_facts(self):
        payload = {"trial": "测试" * 250, "messages": [{"sender": "测试者", "text": "周末读书？"}]}
        result = local_rehearsal(normalize_request(payload))
        self.assertEqual(result["scene_id"], "custom")
        self.assertNotIn("300", json.dumps(result, ensure_ascii=False))
        self.assertNotIn("12点", json.dumps(result, ensure_ascii=False))
        self.assertLessEqual(len(result["routes"][0]["draft"]), 500)

    def test_invalid_request_boundaries(self):
        for payload in [None, [], {}, {"trial": " "}, {"trial": "a" * 501},
                        {"trial": "x", "messages": []}, {"trial": "x", "messages": [None]},
                        {"trial": "x", "messages": [{"sender": "x", "text": "y"}] * 21}]:
            with self.assertRaises(AppError):
                normalize_request(payload)
        payload = request_for(mode="minimax"); payload["consent"] = False
        with self.assertRaises(AppError) as cm:
            normalize_request(payload)
        self.assertEqual(cm.exception.code, "consent_required")

    def test_model_rejects_fabricated_source_quotes(self):
        payload = normalize_request(request_for())
        result = local_rehearsal(payload)
        result["routes"][0]["evidence"][0]["quote"] = "我已经同意了"
        with self.assertRaises(AppError):
            parse_model_result(json.dumps(result), payload["messages"])
        result = local_rehearsal(payload)
        result["routes"][0]["evidence"][0]["message_id"] = True
        with self.assertRaises(AppError):
            parse_model_result(json.dumps(result), payload["messages"])

    def test_model_rejects_incomplete_routes(self):
        payload = normalize_request(request_for())
        for content in ["not JSON", "[]", '{"summary":"test","routes":[]}', '{"routes":[]}']:
            with self.assertRaises(AppError):
                parse_model_result(content, payload["messages"])

    def test_provider_contract_and_thinking_split(self):
        payload = normalize_request(request_for(mode="minimax"))
        output = local_rehearsal(payload)
        fake = FakeOpener("<think>internal test text</think>\n```json\n" + json.dumps(output) + "\n```")
        result = MiniMaxProvider("test-only-fake-key", opener=fake).rehearse(payload)
        sent = json.loads(fake.request.data)
        self.assertEqual(fake.request.full_url, "https://api.minimax.cn/v1/chat/completions")
        self.assertEqual(sent["messages"][0]["role"], "system")
        self.assertEqual(sent["max_completion_tokens"], 8192)
        self.assertFalse(sent["stream"])
        self.assertEqual(result["mode"], "minimax")
        self.assertEqual(result["total_tokens"], 123)
        self.assertNotIn("internal test text", json.dumps(result))

    def test_provider_errors_do_not_become_demo_results(self):
        payload = normalize_request(request_for(mode="minimax"))
        for status in [401, 403, 429, 500]:
            with self.assertRaises(AppError):
                MiniMaxProvider("test-only-fake-key", opener=FakeOpener("", status=status)).rehearse(payload)
        with self.assertRaises(AppError) as cm:
            MiniMaxProvider().rehearse(payload)
        self.assertEqual(cm.exception.code, "model_unconfigured")
        with self.assertRaises(AppError):
            MiniMaxProvider("test-only-fake-key", opener=FakeOpener("{}", finish="length")).rehearse(payload)

    def test_provider_cannot_send_key_to_arbitrary_hosts(self):
        for url in ["http://api.minimax.cn/v1", "https://evil.example/v1", "https://api.minimax.cn.evil.example/v1",
                    "https://api.minimax.cn/v1?token=x", "https://api.minimax.cn:444/v1", "https://x@api.minimax.cn/v1"]:
            with self.assertRaises(ValueError):
                MiniMaxProvider("test-only-fake-key", base_url=url)

    def test_realistic_model_output_can_warn_about_unconfirmed_details(self):
        route = {"draft": "明早9点出发住一晚？", "replies": ["这样人均大概200多能搞定。"]}
        warnings = route_warnings(route, SCENES[0]["messages"])
        self.assertEqual(len(warnings), 3)
        self.assertTrue(any("12点" in x for x in warnings))
        self.assertTrue(any("费用" in x for x in warnings))

    def test_aligned_draft_has_no_known_scene_warning(self):
        route = {"draft": "12点后出发、当天回，预算目标300，费用仍需核实。", "replies": ["先查路线吧。"]}
        self.assertEqual(route_warnings(route, SCENES[0]["messages"]), [])

    def test_live_result_flags_lodging_against_same_day_return(self):
        # Reproduce route B from the actual G2 model response, without relying on repo evidence files.
        value = local_rehearsal(normalize_request(request_for()))
        value["routes"][1].update({
            "replies": ["周五晚出发的话，住宿费能控制在预算里吗", "那周五晚走，周六晚上回来能行吗"],
            "draft": "周五晚出发的话，大家预算和时间都能接受吗？七喜300够不够来回加住宿，阿柚晚上出发方便吗？"})
        result = parse_model_result(json.dumps(value), SCENES[0]["messages"])
        self.assertTrue(any("当天返回" in warning for warning in result["routes"][1]["warnings"]))

    def test_return_reminder_works_for_real_room_text_and_ignores_negation(self):
        route = {"draft": "先查住宿费，第二天再回来？", "replies": ["先重新确认返程吧。"]}
        source = [{"id": 7, "sender": "测试者", "text": "我想当天返回，具体时间还没定。"}]
        self.assertTrue(any("#7" in warning for warning in route_warnings(route, source)))
        source[0]["text"] = "不用当天返回，时间宽松。"
        self.assertEqual(route_warnings(route, source), [])
        source[0]["text"] = "我想当天返回。"
        route = {"draft": "不用住宿，不要过夜，当天回。", "replies": ["先查当天返程路线。"]}
        self.assertEqual(route_warnings(route, source), [])


class HttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.token = "test-only-access-token-0123456789"
        cls.server = OnCueServer(("127.0.0.1", 0), token=cls.token, provider=MiniMaxProvider())
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True); cls.thread.start()
        cls.base = "http://127.0.0.1:" + str(cls.server.server_port)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown(); cls.server.server_close(); cls.thread.join(timeout=2)

    def call(self, path, data=None, cookie=None, headers=None):
        headers = {"Content-Type": "application/json", **(headers or {})}
        if cookie: headers["Cookie"] = cookie
        req = urllib.request.Request(self.base + path, None if data is None else json.dumps(data).encode(), headers)
        try:
            with urllib.request.urlopen(req, timeout=3) as resp:
                return resp.status, resp.headers, json.loads(resp.read()) if path.startswith("/api") else resp.read()
        except urllib.error.HTTPError as e:
            return e.code, e.headers, json.loads(e.read())

    def login(self):
        code, headers, value = self.call("/api/login", {"token": self.token})
        self.assertEqual(code, 200)
        self.assertIn("HttpOnly", headers["Set-Cookie"])
        return headers["Set-Cookie"].split(";")[0]

    def test_auth_required_for_data_and_calls(self):
        self.assertEqual(self.call("/api/scenes")[0], 401)
        self.assertEqual(self.call("/api/rehearse", request_for())[0], 401)
        self.assertEqual(self.call("/api/login", {"token": "wrong"})[0], 401)
        code, headers, value = self.call("/api/status")
        self.assertFalse(value["authenticated"])

    def test_login_rehearse_and_logout(self):
        cookie = self.login()
        self.assertEqual(self.call("/api/scenes", cookie=cookie)[0], 200)
        code, headers, value = self.call("/api/rehearse", request_for(), cookie)
        self.assertEqual(code, 200); self.assertEqual(len(value["result"]["routes"]), 3)
        self.assertEqual(headers["Cache-Control"], "no-store")
        self.assertEqual(self.call("/api/logout", {}, cookie)[0], 200)
        self.assertEqual(self.call("/api/scenes", cookie=cookie)[0], 401)

    def test_origin_host_and_paths(self):
        cookie = self.login()
        self.assertEqual(self.call("/api/rehearse", request_for(), cookie, {"Origin": "https://evil.example"})[0], 403)
        self.assertEqual(self.call("/api/status", headers={"Host": "evil.example"})[0], 403)
        self.assertEqual(self.call("/../engine.py")[0], 404)
        self.assertEqual(self.call("/.env")[0], 404)

    def test_missing_provider_and_consent_are_distinct(self):
        cookie = self.login(); payload = request_for(mode="minimax")
        code, _, value = self.call("/api/rehearse", payload, cookie)
        self.assertEqual(code, 503); self.assertEqual(value["error"]["code"], "model_unconfigured")
        payload["consent"] = False
        self.assertEqual(self.call("/api/rehearse", payload, cookie)[0], 400)


if __name__ == "__main__":
    unittest.main()
