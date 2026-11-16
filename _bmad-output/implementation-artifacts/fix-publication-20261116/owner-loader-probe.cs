using System.Reflection;
using System.Reflection.Emit;
using System.Runtime.Loader;
using Hexalith.Projects.PackageFixtures.AppHost;

string root = Path.Combine(Path.GetTempPath(), "owner-loader-probe-" + Guid.NewGuid().ToString("N"));
Directory.CreateDirectory(root);
try
{
    string owner = Path.Combine(root, "Owner.dll");
    Write(owner, "Owner", 1);
    var changed = new PackageOwnerLoadContext(owner);
    Assembly first = changed.LoadOwner(owner);
    File.Move(owner, owner + ".old");
    Write(owner, "Owner", 2);
    Refused(() => changed.LoadOwner(owner), "changed after loading");
    Require(Read(first) == 1, "cached original image changed");
    Console.WriteLine("PASS: replacement of a loaded path refuses");

    string defaults = Path.Combine(root, "defaults"), selected = Path.Combine(root, "selected");
    Directory.CreateDirectory(defaults); Directory.CreateDirectory(selected);
    string leafPath = Path.Combine(defaults, "Leaf.dll"), middlePath = Path.Combine(defaults, "Middle.dll");
    Write(leafPath, "Leaf", 1);
    Assembly leaf = AssemblyLoadContext.Default.LoadFromAssemblyPath(leafPath);
    Write(middlePath, "Middle", 0, leaf.GetType("Probe")!.GetMethod("Read"));
    Assembly middle = AssemblyLoadContext.Default.LoadFromAssemblyPath(middlePath);
    Require(Read(middle) == 1, "default graph baseline is incorrect");
    File.Copy(middlePath, Path.Combine(selected, "Middle.dll"));
    Write(Path.Combine(selected, "Leaf.dll"), "Leaf", 2);
    string outer = Path.Combine(selected, "Outer.dll");
    Write(outer, "Outer", 0, middle.GetType("Probe")!.GetMethod("Read"));
    var closure = new PackageOwnerLoadContext(outer);
    Require(Read(closure.LoadOwner(outer)) == 2, "selected graph reused the default leaf");
    Console.WriteLine("PASS: identical intermediate library keeps the selected dependency graph");

    string link = Path.Combine(selected, "Linked.dll");
    File.CreateSymbolicLink(link, owner);
    var links = new PackageOwnerLoadContext(link);
    Refused(() => links.LoadOwner(link), "regular output file");
    Console.WriteLine("PASS: output-local link to an outside owner refuses");

    string linkedDirectory = Path.Combine(selected, "linked-directory");
    Directory.CreateSymbolicLink(linkedDirectory, defaults);
    Refused(() => links.LoadOwner(Path.Combine(linkedDirectory, "Leaf.dll")), "linked directories");
    Console.WriteLine("PASS: output-local directory link refuses");

    string sdkName = "Hexalith.EventStore.FixtureProbe";
    string sdkOriginal = Path.Combine(defaults, sdkName + ".dll"), sdkSelected = Path.Combine(selected, sdkName + ".dll");
    Write(sdkOriginal, sdkName, 1);
    Assembly actualSdk = AssemblyLoadContext.Default.LoadFromAssemblyPath(sdkOriginal);
    File.Move(sdkOriginal, sdkOriginal + ".old");
    Write(sdkOriginal, sdkName, 2);
    File.Copy(sdkOriginal, sdkSelected);
    var sdkContext = new PackageOwnerLoadContext(outer);
    try { sdkContext.LoadFromAssemblyName(actualSdk.GetName()); throw new InvalidOperationException("Stale SDK image was accepted"); }
    catch (FileLoadException error) when (error.InnerException is InvalidOperationException refusal
        && refusal.Message.Contains("actual module", StringComparison.Ordinal)) { }
    Console.WriteLine("PASS: matching on-disk SDK hashes cannot mask a stale loaded image");
}
finally { Directory.Delete(root, recursive: true); }

static int Read(Assembly assembly) => (int)assembly.GetType("Probe")!.GetMethod("Read")!.Invoke(null, null)!;
static void Require(bool condition, string message) { if (!condition) throw new InvalidOperationException(message); }
static void Refused(Action action, string expected)
{
    try { action(); }
    catch (InvalidOperationException error) when (error.Message.Contains(expected, StringComparison.Ordinal)) { return; }
    throw new InvalidOperationException("Expected refusal: " + expected);
}
static void Write(string path, string name, int value, MethodInfo? next = null)
{
    var assembly = new PersistedAssemblyBuilder(new AssemblyName(name) { Version = new Version(1, 0, 0, 0) }, typeof(object).Assembly);
    ModuleBuilder module = assembly.DefineDynamicModule(name);
    TypeBuilder type = module.DefineType("Probe", TypeAttributes.Public | TypeAttributes.Abstract | TypeAttributes.Sealed);
    MethodBuilder method = type.DefineMethod("Read", MethodAttributes.Public | MethodAttributes.Static, typeof(int), Type.EmptyTypes);
    ILGenerator il = method.GetILGenerator();
    if (next is null) il.Emit(OpCodes.Ldc_I4, value);
    else il.Emit(OpCodes.Call, next);
    il.Emit(OpCodes.Ret);
    _ = type.CreateType();
    using var output = new FileStream(path, FileMode.CreateNew, FileAccess.Write);
    assembly.Save(output);
}
