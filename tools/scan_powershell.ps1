# Parse stdin as data. Never invoke, import or dot-source the submitted text.
$ErrorActionPreference = 'Stop'
$source = [Console]::In.ReadToEnd()
# ModuleAnalysis avoids post-parse symbol resolution and host module lookup.
# https://github.com/PowerShell/PowerShell/blob/v7.6.2/src/System.Management.Automation/engine/parser/Parser.cs
# This internal API is checked at runtime; incompatible runtimes fail closed.
$parserType = [System.Management.Automation.Language.Parser]
$parser = [Activator]::CreateInstance($parserType, $true)
$modeType = $parserType.Assembly.GetType('System.Management.Automation.Language.ParseMode', $true)
$mode = [Enum]::Parse($modeType, 'ModuleAnalysis')
$tokens = [System.Collections.Generic.List[System.Management.Automation.Language.Token]]::new()
$arguments = [object[]]@($null, $source, $tokens, $null, $mode)
$parse = $parserType.GetMethod('Parse', [System.Reflection.BindingFlags]'Instance,NonPublic')
$tree = $parse.Invoke($parser, $arguments)
$parseErrors = $arguments[3]
$events = [System.Collections.Generic.List[object]]::new()
foreach ($issue in $parseErrors) {
    $events.Add(@{ kind = 'error'; line = $issue.Extent.StartLineNumber; text = $issue.Message })
}
foreach ($requirement in $tree.ScriptRequirements.RequiredModules) {
    $requireLine = @($tokens | Where-Object { $_.Text -match '^#requires\s+-modules\b' } |
        Select-Object -First 1)
    $line = if ($requireLine.Count) { $requireLine[0].Extent.StartLineNumber } else { 1 }
    $events.Add(@{ kind = 'module'; line = $line; text = $requirement.Name })
}
foreach ($node in $tree.FindAll({ param($ast) $true }, $true)) {
    $line = $node.Extent.StartLineNumber
    if ($node -is [System.Management.Automation.Language.CommandAst]) {
        $words = @($node.CommandElements | ForEach-Object {
            $operand = $_
            if ($_ -is [System.Management.Automation.Language.CommandParameterAst] -and $null -ne $_.Argument) {
                @{ type = 'CommandParameterAst'; value = '-' + $_.ParameterName; splatted = $false; computed = $false }
                $operand = $_.Argument
            }
            $value = $operand.Extent.Text
            if ($operand -is [System.Management.Automation.Language.StringConstantExpressionAst] -or
                $operand -is [System.Management.Automation.Language.ExpandableStringExpressionAst]) {
                $value = $operand.Value
            }
            @{ type = $operand.GetType().Name; value = $value;
                splatted = ($operand -is [System.Management.Automation.Language.VariableExpressionAst] -and $operand.Splatted);
                computed = ($operand -isnot [System.Management.Automation.Language.StringConstantExpressionAst] -and
                    $operand -isnot [System.Management.Automation.Language.ExpandableStringExpressionAst] -and
                    $operand -isnot [System.Management.Automation.Language.ConstantExpressionAst] -and
                    $operand -isnot [System.Management.Automation.Language.VariableExpressionAst] -and
                    $operand -isnot [System.Management.Automation.Language.ScriptBlockExpressionAst] -and
                    $operand -isnot [System.Management.Automation.Language.CommandParameterAst]) }
        })
        $events.Add(@{ kind = 'command'; line = $line; words = $words;
            invocation = $node.InvocationOperator.ToString(); text = $node.Extent.Text;
            redirects = @($node.Redirections | ForEach-Object { $_.Extent.Text }) })
    }
    elseif ($node -is [System.Management.Automation.Language.StringConstantExpressionAst] -or
            $node -is [System.Management.Automation.Language.ExpandableStringExpressionAst]) {
        $events.Add(@{ kind = 'literal'; line = $line; text = $node.Value })
        if ($node -is [System.Management.Automation.Language.ExpandableStringExpressionAst] -and
            $node.StringConstantType.ToString() -eq 'DoubleQuotedHereString' -and
            $node.NestedExpressions.Count -gt 0) {
            $events.Add(@{ kind = 'here-expansion'; line = $line + 1; text = '' })
        }
    }
    elseif ($node -is [System.Management.Automation.Language.AssignmentStatementAst] -or
            ($node -is [System.Management.Automation.Language.UnaryExpressionAst] -and
             $node.TokenKind.ToString() -in @('PlusPlus', 'MinusMinus', 'PostfixPlusPlus', 'PostfixMinusMinus'))) {
        $increment = $node -is [System.Management.Automation.Language.UnaryExpressionAst]
        $left = if ($increment) { $node.Child } else { $node.Left }
        $target = $left
        while ($left -is [System.Management.Automation.Language.ConvertExpressionAst]) { $left = $left.Child }
        $variables = @($target.FindAll({ param($ast)
            $ast -is [System.Management.Automation.Language.VariableExpressionAst]
        }, $true) | ForEach-Object { $_.VariablePath.UserPath })
        $events.Add(@{ kind = 'assignment'; line = $line; text = $node.Extent.Text;
            variables = $variables; increment = $increment;
            operator = $(if ($increment) { $node.TokenKind.ToString() } else { $node.Operator.ToString() });
            simple = ($left -is [System.Management.Automation.Language.VariableExpressionAst]) })
    }
    elseif ($node -is [System.Management.Automation.Language.InvokeMemberExpressionAst]) {
        $events.Add(@{ kind = 'member'; line = $line; text = $node.Extent.Text })
    }
    elseif ($node -is [System.Management.Automation.Language.UsingStatementAst] -and
            $node.UsingStatementKind.ToString() -eq 'Module') {
        if ($null -ne $node.Name) {
            $events.Add(@{ kind = 'module'; line = $line; text = $node.Name.Value })
        }
        else {
            $names = @($node.ModuleSpecification.KeyValuePairs | Where-Object { $_.Item1.Value -eq 'ModuleName' })
            $value = if ($names.Count -eq 1) { $names[0].Item2 } else { $null }
            if ($null -ne $value -and $value -is [System.Management.Automation.Language.PipelineAst] -and
                $value.PipelineElements.Count -eq 1 -and
                $value.PipelineElements[0] -is [System.Management.Automation.Language.CommandExpressionAst] -and
                $value.PipelineElements[0].Expression -is
                    [System.Management.Automation.Language.StringConstantExpressionAst]) {
                $events.Add(@{ kind = 'module'; line = $line;
                    text = $value.PipelineElements[0].Expression.Value })
            }
            else {
                $events.Add(@{ kind = 'unsupported'; line = $line; text = 'unresolved PowerShell module specification' })
            }
        }
    }
    elseif ($node -is [System.Management.Automation.Language.ArrayLiteralAst] -or
            $node -is [System.Management.Automation.Language.ArrayExpressionAst]) {
        $values = @($node.FindAll({ param($ast)
            $ast -is [System.Management.Automation.Language.StringConstantExpressionAst]
        }, $true) | ForEach-Object { $_.Value })
        $events.Add(@{ kind = 'sequence'; line = $line; values = $values })
    }
}
ConvertTo-Json -InputObject @{ events = @($events) } -Depth 8 -Compress
