# Contributing

Explain the problem and resulting behavior in a pull request. Include relevant
validation and limits. Small, reviewable changes make privacy and correctness
easier to assess.

Read [AGENTS.md](AGENTS.md) and the [publication procedure](docs/publication.md)
before adding content. Use synthetic data in tests. Do not attach a real memory
archive, secret, account diagnostic, or personal conversation to an issue or pull
request.

Concept changes should explain the proposed wording and meaning, its relation to
the existing foundation, and the reasoning behind the change. Keep personal
teaching histories in their authorized private stores. Update the JSON source
and regenerate `foundation/concepts.md` using `scripts/render_concepts.py`.

Code changes should preserve fresh-instance isolation, fail visibly on incomplete
operations, and distinguish storage success from retrieval and host behavior.
Run the unit tests and public-content check. Schema changes also require a
disposable-database check and a migration design for existing instances.

The repository's existing GPLv3 license applies to contributions. Document the
license and origin of any third-party material you propose to include.
