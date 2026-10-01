from insurance_ai.services.gemini_manager import GeminiModelManager


class Resp:
    def __init__(self, text): self.text=text


class Models:
    def __init__(self): self.calls=[]
    def generate_content(self, model, contents, **kwargs):
        self.calls.append(model)
        if model == "bad-model": raise RuntimeError("busy")
        return Resp('{"operation":"describe"}' if kwargs else "ok")


class Client:
    def __init__(self): self.models=Models()


def test_model_fallback():
    client=Client()
    mgr=GeminiModelManager(api_key="x",models=["bad-model","good-model"],max_retries=0,client=client)
    r=mgr.generate("hello")
    assert r.text == "ok"
    assert r.model == "good-model"
    assert r.fallback_used is True
    assert client.models.calls == ["bad-model","good-model"]
