import argparse

from animegen.pipeline import STAGES, run_pipeline


def main():
    parser = argparse.ArgumentParser(description="Convert webtoon chapters to animated videos")
    parser.add_argument("url", help="Webtoon series URL")
    parser.add_argument("chapter", type=int, help="Chapter number to process")
    parser.add_argument("--config", default="config.yaml", help="Path to config file")
    parser.add_argument("--start-stage", default="download", choices=STAGES,
                        help="Stage to start from (default: download)")
    parser.add_argument("--end-stage", default="assemble", choices=STAGES,
                        help="Stage to stop at (default: assemble)")
    args = parser.parse_args()

    run_pipeline(args.url, args.chapter, args.config, args.start_stage, args.end_stage)
