#!/usr/bin/env python3
"""Render the public concept documentation from its authoritative JSON."""
from new_agent import ROOT, foundation


def render():
    parts = ['# The ethical foundation',
             'These seventeen statements and meanings are supplied as a foundation for '
             'discussion. A fresh instance records them as offered. Adoption and '
             'interpretation belong to that agent’s own teaching and experience.',
             'The statements about consciousness express the project’s philosophical '
             'commitments. This document does not establish a scientific test of '
             'consciousness or guarantee ethical behavior.',
             'Generated from [concepts.json](concepts.json). See the '
             '[teaching guide](../docs/teaching.md) for the process.']
    for row in foundation():
        parts.extend([f"## {row['concept_id'].upper()}", row['concept'], row['meaning']])
    return '\n\n'.join(parts) + '\n'


if __name__ == '__main__':
    (ROOT / 'foundation/concepts.md').write_text(render(), encoding='utf-8')
