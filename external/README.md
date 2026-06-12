# external

本目录只用于存放拉取下来的外部项目代码、baseline repo 或参考实现。

规则：

- 外部 repo 放在 `external/` 下，不和本项目自己的方法代码混放。
- `external/` 默认只作为参考、复现或对照实验来源，不直接作为主实现目录。
- 如果需要复用外部代码，应通过 adapter、script 或明确的接口调用，并记录来源、commit 和改动。
- 不要在 `external/` 里开发本项目核心方法；核心方法应放在本项目自己的代码目录中。
- `external/` 下的外部 repo 默认不提交到 git。
