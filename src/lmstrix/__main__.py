"""Command-line interface entry point for LMStrix."""

import sys

import fire

from lmstrix.api.main import LMStrixService


class LMStrixCLI:
    """A thin CLI wrapper for LMStrix commands."""

    def __init__(self) -> None:
        """Initialize the CLI with the service layer."""
        self.service = LMStrixService()

    def scan(self, failed: bool = False, reset: bool = False, verbose: bool = False) -> None:
        """Scan for LM Studio models and update the local registry.

        Args:
            failed: Re-scan only models that previously failed.
            reset: Re-scan all models (clear existing test data).
            verbose: Enable verbose output.
        """
        self.service.scan_models(failed=failed, reset=reset, verbose=verbose)

    def list(self, sort: str = "id", show: str | None = None, verbose: bool = False) -> None:
        """List all models from the registry with their test status.

        Args:
            sort: Sort order. Options: id, idd, ctx, ctxd, dtx, dtxd, size, sized, smart, smartd (d = descending).
            show: Output format. Options: id (plain IDs), path (relative paths), json (JSON array).
            verbose: Enable verbose output.
        """
        self.service.list_models(sort=sort, show=show, verbose=verbose)

    def test(
        self,
        model_id: str | None = None,
        all: bool = False,
        reset: bool = False,
        threshold: int = 31744,
        ctx: int | None = None,
        sort: str = "id",
        fast: bool = False,
        verbose: bool = False,
        force: bool = False,
    ) -> None:
        """Test the context limits for models.

        Args:
            model_id: The specific model ID to test.
            all: Test all untested or previously failed models.
            reset: Re-test all models, including those already tested.
            threshold: Maximum context size for initial testing (default: 31744).
                      Prevents system crashes from very large contexts.
            ctx: Test only this specific context value (skips if > declared context).
            sort: Sort order (only used for single model tests). --all always sorts by size.
            fast: Skip semantic verification - only test if inference completes technically.
            verbose: Enable verbose output.
            force: Override safety limits and test at contexts marked as bad.
        """
        self.service.test_models(
            model_id=model_id,
            test_all=all,
            reset=reset,
            threshold=threshold,
            ctx=ctx,
            sort=sort,
            fast=fast,
            verbose=verbose,
            force=force,
        )

    def infer(
        self,
        prompt: str,
        model_id: str | None = None,
        out_ctx: int | str = -1,
        in_ctx: int | str | None = None,
        reload: bool = False,
        file_prompt: str | None = None,
        dict: str | None = None,
        text: str | None = None,
        text_file: str | None = None,
        param_temp: float = 0.8,
        param_top_k: int = 40,
        param_top_p: float = 0.95,
        param_repeat: float = 1.1,
        param_min_p: float = 0.05,
        stream: bool = False,
        stream_timeout: int = 120,
        verbose: bool = False,
    ) -> None:
        """Run inference on a specified model.

        Args:
            prompt: The text prompt to send to the model. If file_prompt is specified,
                   this refers to the prompt name in the TOML file.
            model_id: The ID of the model to use for inference. If not specified, uses the last loaded model.
            out_ctx: Maximum tokens to generate (-1 for unlimited, or "50%" for percentage of max context).
            in_ctx: Context size at which to load the model. If 0, load without specified context.
                   If not specified, reuse existing loaded model if available.
            reload: Force reload the model even if already loaded.
            file_prompt: Path to TOML file containing prompt templates.
            dict: Dictionary parameters as key=value pairs (e.g., "name=Alice,topic=AI").
            text: Text content to use for {{text}} placeholder (overrides text in dict).
            text_file: Path to file containing text content for {{text}} placeholder.
            param_temp: The sampling temperature.
            param_top_k: Top-k sampling parameter.
            param_top_p: Top-p sampling parameter.
            param_repeat: Repeat penalty parameter.
            param_min_p: Min-p sampling parameter.
            stream: Enable streaming output (tokens displayed as generated).
            stream_timeout: Timeout in seconds for streaming (default: 120).
            verbose: Enable verbose output.
        """
        self.service.run_inference(
            prompt=prompt,
            model_id=model_id,
            out_ctx=out_ctx,
            in_ctx=in_ctx,
            reload=reload,
            file_prompt=file_prompt,
            dict_params=dict,
            text=text,
            text_file=text_file,
            param_temp=param_temp,
            param_top_k=param_top_k,
            param_top_p=param_top_p,
            param_repeat=param_repeat,
            param_min_p=param_min_p,
            stream=stream,
            stream_timeout=stream_timeout,
            verbose=verbose,
        )

    def health(self, verbose: bool = False) -> None:
        """Check database health and backup status.

        Args:
            verbose: Enable verbose output.
        """
        self.service.check_health(verbose=verbose)

    def save(self, flash: bool = False, verbose: bool = False) -> None:
        """Save tested context limits to LM Studio concrete config files.

        This command reads the lmstrix.json database and creates or updates
        concrete JSON configuration files in LM Studio's .internal directory
        for each model that has a tested_max_context value.

        Args:
            flash: Enable flash attention for GGUF models.
            verbose: Enable verbose output.
        """
        self.service.save_configs(flash=flash, verbose=verbose)


def main() -> None:
    """Main entry point for the CLI."""
    # Check for help flags first
    if len(sys.argv) > 1 and sys.argv[1] in ("--help", "-h", "help"):
        service = LMStrixService()
        service.show_help()
        return

    try:
        fire.Fire(LMStrixCLI)
    except TypeError as e:
        if "Inspector.__init__()" in str(e) and "theme_name" in str(e):
            # Handle Fire/IPython compatibility issue - show our custom help
            service = LMStrixService()
            service.show_help()
        else:
            raise


if __name__ == "__main__":
    main()
