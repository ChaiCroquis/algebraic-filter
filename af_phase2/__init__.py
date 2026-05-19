"""algebraic-filter Phase 2: 関数シグネチャから代数法則を推論して PBT 自動生成。

Phase 1 で landed した 46 sample (samples/violations/) を input として、
関数名 + 型シグネチャから期待法則を推論し、 hypothesis @given test を自動生成する。

Modules:
  inferrer: 関数 → list[Law] 推論
  law_templates: Monoid / Functor / Commutativity / Monad の標準法則テンプレ
  generator: 推論結果 + テンプレ → @given test 関数 (or test file) 生成
"""

__version__ = "0.1.0-phase2-prototype"
