from orchestrator.utils.logger import get_logger
from orchestrator.pipeline import start_pipeline
from orchestrator.settings import settings

logger = get_logger(__name__)

if __name__ == "__main__":
    logger.info("=" * 80)
    logger.info("INSTALLED PYTHON PACKAGES")
    logger.info("=" * 80)
    try:
        from importlib.metadata import distributions
        installed_packages = [(d.metadata.get('Name', 'Unknown'), d.version) for d in distributions()]
    except ImportError:
        try:
            import pkg_resources
            installed_packages = [(d.project_name, d.version) for d in pkg_resources.working_set]
        except Exception:
            logger.warning("Could not retrieve installed packages list")
            installed_packages = []
    
    installed_packages.sort()
    for package_name, package_version in installed_packages:
        logger.info(f"  {package_name}=={package_version}")
    logger.info("=" * 80)
    logger.info(f"Total packages: {len(installed_packages)}")
    logger.info("=" * 80)


    logger.info("Starting WhoScored orchestration pipeline")
    logger.info(f"Settings: {settings.model_dump()}")
    start_pipeline()
