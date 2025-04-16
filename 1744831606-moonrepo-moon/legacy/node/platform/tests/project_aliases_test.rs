// TODO: These tests require a full workspace including platforms. Redo them!

// use moon_common::Id;
// use moon_project_graph::ProjectGraph;
// use moon_test_utils::{
//     assert_snapshot, create_sandbox_with_config, get_project_graph_aliases_fixture_configs, Sandbox,
// };
// use moon_test_utils2::generate_project_graph_from_sandbox;
// use rustc_hash::FxHashMap;

// async fn get_aliases_graph() -> (ProjectGraph, Sandbox) {
//     let (workspace_config, toolchain_config, tasks_config) =
//         get_project_graph_aliases_fixture_configs();

//     let sandbox = create_sandbox_with_config(
//         "project-graph/aliases",
//         Some(workspace_config),
//         Some(toolchain_config),
//         Some(tasks_config),
//     );

//     let graph = generate_project_graph_from_sandbox(sandbox.path()).await;

//     (graph, sandbox)
// }

// #[tokio::test(flavor = "multi_thread")]
// async fn loads_node_aliases_name_scopes() {
//     let (graph, _sandbox) = get_aliases_graph().await;

//     assert_eq!(
//         graph.aliases(),
//         FxHashMap::from_iter([
//             ("project-graph-aliases-explicit", &Id::raw("explicit")),
//             (
//                 "project-graph-aliases-explicit-and-implicit",
//                 &Id::raw("explicitAndImplicit")
//             ),
//             ("project-graph-aliases-implicit", &Id::raw("implicit")),
//             ("project-graph-aliases-node", &Id::raw("node")),
//             ("pkg-bar", &Id::raw("nodeNameOnly")),
//             ("@scope/pkg-foo", &Id::raw("nodeNameScope"))
//         ])
//     );
// }

// #[tokio::test(flavor = "multi_thread")]
// async fn returns_project_using_alias() {
//     let (graph, _sandbox) = get_aliases_graph().await;

//     assert_eq!(
//         graph.get("@scope/pkg-foo").unwrap().id,
//         "nodeNameScope".to_owned()
//     );
// }

// #[tokio::test(flavor = "multi_thread")]
// async fn graph_uses_id_for_nodes() {
//     let (graph, _sandbox) = get_aliases_graph().await;

//     graph.get("pkg-bar").unwrap();
//     graph.get("@scope/pkg-foo").unwrap();

//     assert_snapshot!(graph.to_dot());
// }
