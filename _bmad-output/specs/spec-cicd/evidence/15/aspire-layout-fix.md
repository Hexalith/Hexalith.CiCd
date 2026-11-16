# Authenticated Aspire setup layout correction

The real hosted native sample failed at verified Aspire CLI 13.6.5 setup with exit 6 after extraction. The original completed-job log is retained in builds-native-sample-failure.log (run 43913170549, job 133460203350). Dapr initialization, exact runtime inventory and the hosted namespace adjustment/reprobe had succeeded. Extracted files alone were never accepted as successful setup.

Pinned upstream SetupCommand and LayoutDiscovery establish that custom install roots require ASPIRE_LAYOUT_PATH. The setup process performs layout discovery after extraction and otherwise may discover a different existing layout or fail on a fresh runner. The fix supplies the supported variable only to each bounded setup subprocess, equal to that invocation's exact --install-path root. It preserves fatal nonzero exits and the complete embedded bundle comparison.

Sources: [SetupCommand](https://github.com/microsoft/aspire/blob/v13.6.5/src/Aspire.Cli/Commands/SetupCommand.cs), [LayoutDiscovery](https://github.com/microsoft/aspire/blob/v13.6.5/src/Aspire.Cli/Layout/LayoutDiscovery.cs), [BundleService](https://github.com/microsoft/aspire/blob/v13.6.5/src/Aspire.Cli/Bundles/BundleService.cs).

aspire-supported-layout-qualification.log records two actual authenticated private setup invocations, each returning 0, and comparison of all 490 bundle files. It leaves HOME, home and CODEX_HOME untouched. Both interpreter runs of the 30 shared environment tests passed, including an assertion that every setup invocation carries its exact target variable. This is local installer qualification; the new hosted native sample and acceptable shared release still require actual green CI.

The earlier reproduction mistakenly supplied a disposable child HOME. That failed run is explicitly retained as aspire-setup-home-override-not-qualification.log and is not qualification evidence. The helper was corrected before the supported-variable qualification; no host credential or configuration file was read or modified by that reproduction.
