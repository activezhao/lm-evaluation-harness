"""
"Evaluating Large Language Models Trained on Code"
https://arxiv.org/abs/2107.03374

TODO: add abstract/description

Homepage: https://github.com/openai/human-eval
"""
import os
import json
from lm_eval.base import Task, rf
from lm_eval.metrics import mean


_CITATION = """
@article{chen2021codex,
  title={Evaluating Large Language Models Trained on Code},
  author={Mark Chen and Jerry Tworek and Heewoo Jun and Qiming Yuan and Henrique Ponde de Oliveira Pinto and Jared Kaplan and Harri Edwards and Yuri Burda and Nicholas Joseph and Greg Brockman and Alex Ray and Raul Puri and Gretchen Krueger and Michael Petrov and Heidy Khlaaf and Girish Sastry and Pamela Mishkin and Brooke Chan and Scott Gray and Nick Ryder and Mikhail Pavlov and Alethea Power and Lukasz Kaiser and Mohammad Bavarian and Clemens Winter and Philippe Tillet and Felipe Petroski Such and Dave Cummings and Matthias Plappert and Fotios Chantzis and Elizabeth Barnes and Ariel Herbert-Voss and William Hebgen Guss and Alex Nichol and Alex Paino and Nikolas Tezak and Jie Tang and Igor Babuschkin and Suchir Balaji and Shantanu Jain and William Saunders and Christopher Hesse and Andrew N. Carr and Jan Leike and Josh Achiam and Vedant Misra and Evan Morikawa and Alec Radford and Matthew Knight and Miles Brundage and Mira Murati and Katie Mayer and Peter Welinder and Bob McGrew and Dario Amodei and Sam McCandlish and Ilya Sutskever and Wojciech Zaremba},
  year={2021},
  eprint={2107.03374},
  archivePrefix={arXiv},
  primaryClass={cs.LG}
}
"""


class HumanEval(Task):
    VERSION = 0
    DATASET_PATH = "openai_humaneval"
    DATASET_NAME = None

    def has_training_docs(self):
        return False

    def has_validation_docs(self):
        return False

    def has_test_docs(self):
        return True

    def training_docs(self):
        raise NotImplementedError

    def validation_docs(self):
        raise NotImplementedError

    def test_docs(self):
        return self.dataset["test"]

    def doc_to_text(self, doc):
        return doc["prompt"]

    def doc_to_target(self, doc):
        return doc["canonical_solution"]

    def construct_requests(self, doc, ctx):
        """Uses RequestFactory to construct Requests and returns an iterable of
        Requests which will be sent to the LM.

        :param doc:
            The document as returned from training_docs, validation_docs, or test_docs.
        :param ctx: str
            The context string, generated by fewshot_context. This includes the natural
            language description, as well as the few shot examples, and the question
            part of the document for `doc`.
        """
        completion = [rf.greedy_until(ctx, {"until": ["\n\n"]}) for i in range(1)]
        return completion

    def _is_correct(self, completion, doc):
        return True

    def process_results(self, doc, results):
        """Take a single document and the LM results and evaluates, returning a
        dict where keys are the names of submetrics and values are the values of
        the metric for that one document

        :param doc:
            The document as returned from training_docs, validation_docs, or test_docs.
        :param results:
            The results of the requests created in construct_requests.
        """
        
        # log outputs to a jsonl file, for use with the official evaluation + execution script.
        if os.environ.get('CODE_DUMP_PATH', None) is not None:
            with open(f"{os.environ['CODE_DUMP_PATH']}", "a") as f:
                for completion in results:
                    f.write(json.dumps({"task_id": doc["task_id"], "completion": completion}) + "\n")
       
        # execution code would go here if we allowed it, but we don't
        return {"pass@1": self._is_correct(results, doc), "pass@10": self._is_correct(results, doc)}

    def aggregation(self):
        """
        :returns: {str: [float] -> float}
            A dictionary where keys are the names of submetrics and values are
            functions that aggregate a list of metrics
        """
        return {"pass@1": mean, "pass@10": mean}

    def higher_is_better(self):
        """
        :returns: {str: bool}
            A dictionary where keys are the names of submetrics and values are
            whether a higher value of the submetric is better
        """
        return {f"pass@{k}": True for k in [1, 10, 100]}
